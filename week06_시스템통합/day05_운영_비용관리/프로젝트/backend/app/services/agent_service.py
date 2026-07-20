"""RF-3 AI상담을 Tool을 사용하는 AI Agent로 확장한 서비스.

week04 day04 "AI 에이전트 챗봇 설계 (외부 인터넷 조회 도구)" 문서의 구조를 그대로 따르되,
내부 지식 조회 Tool을 week05에서 만든 RAG(벡터 검색)로 교체한다.
- 내부 지식베이스(상품·영양소 기능성·섭취기준) 조회는 rag_service(Chroma + Ollama 임베딩)를
  Tool로 감싸서 사용한다. week04의 키워드(LIKE) 검색을 의미 기반 검색으로 대체한 것이다.
- 외부 조회는 TavilySearch로 "뉴스"와 "회수·안전성 경보" 두 개 Tool을 그대로 사용한다.
- 모든 Tool은 조회 권한만 가지며, 실행(구매취소·신고접수 등)은 하지 않는다.
"""
import re

from app.core.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    RAG_TOP_K,
    RECALL_ALERT_DOMAINS,
    SUPPLEMENT_NEWS_DOMAINS,
    TAVILY_API_KEY,
)
from app.schemas.chat import ChatMessage, ChatResponse
from app.services import rag_service, usage_service

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")
# search_internal_knowledge 도구가 근거 문서를 인용할 때 다는 표식. ([근거 1] 상품마스터 - 뉴메릿 ...)
_REFERENCE_LABEL_PATTERN = re.compile(r"^\[근거 \d+\] (.+)$", re.MULTILINE)
# search_recall_alert 도구가 실제로 회수·경보를 찾았을 때만 심는 내부 표식(사용자에게는 노출되지 않는다).
_RECALL_FOUND_MARKER = "[[RECALL_FOUND]]"

# day04 설계문서 System Prompt 확장 섹션을 week05 RAG에 맞춰 갱신했다.
_SYSTEM_PROMPT = """당신은 건강기능식품 추천 서비스 '건강한하루'의 AI 상담원입니다.

원칙:
1. 내부 지식베이스(search_internal_knowledge, 벡터 검색·RAG)로 답할 수 있으면 항상 먼저 사용한다.
2. 최신 뉴스, 리콜/회수 여부, 트렌드처럼 내부 지식베이스에 없는 질문만
   search_supplement_news 또는 search_recall_alert 도구를 사용한다.
3. 도구를 사용했다면 반드시 근거를 제시한다. 내부 지식베이스 결과는 "[근거 N] 문서명" 형태 라벨을,
   외부 검색 결과는 출처 URL을 그대로 답변에 포함한다.
4. 도구 결과에도 없는 내용은 확신하듯 말하지 않는다. 모르면 "확인된 자료가 없습니다"라고 답한다.
5. 회수·부작용 경보를 발견하면 반드시 CS 상담 연결을 안내한다(직접 연결하지는 않는다).
6. 의학적 진단, 처방, 구매·신고 대행처럼 조회를 넘어서는 요청은 할 수 없다고 안내하고
   CS 상담 연결을 제안한다.
7. 여러 건의 결과(뉴스, 상품, 기능성 근거 등)를 안내할 때는 마크다운 표(테이블)를 사용하지 말고,
   번호를 매긴 목록 형식으로 작성한다. 각 항목은 "N. 제목" 다음 줄에 "   내용" 형태로 들여써서 쓰고,
   출처 URL은 항목 마지막 줄에 "   출처: URL" 형태로 적는다.
"""


class AgentError(Exception):
    """Agent 호출(LLM/Tool 통신) 중 발생한 오류."""


class AgentNotConfiguredError(AgentError):
    """GROQ_API_KEY / TAVILY_API_KEY 가 설정되지 않아 Agent를 만들 수 없는 상태."""


def _require_config() -> None:
    missing = [
        name
        for name, value in (("GROQ_API_KEY", GROQ_API_KEY), ("TAVILY_API_KEY", TAVILY_API_KEY))
        if not value
    ]
    if missing:
        raise AgentNotConfiguredError(
            "AI 상담 기능을 사용하려면 backend/.env 에 "
            f"{', '.join(missing)} 값을 설정해야 합니다."
        )


def _build_internal_tools():
    from langchain_core.tools import tool

    @tool
    def search_internal_knowledge(질문: str) -> str:
        """건강한하루 내부 지식베이스(상품, 영양소 기능성, 섭취기준)를 벡터 검색(RAG)으로 조회합니다.
        상품 추천, 성분 설명, 섭취기준(권장/상한 섭취량) 관련 질문에는 항상 가장 먼저 시도해야 합니다."""
        try:
            docs = rag_service.search(질문, k=RAG_TOP_K)
        except rag_service.RagNotReadyError as exc:
            return str(exc)

        if not docs:
            return f"내부 지식베이스에서 '{질문}'와(과) 관련된 근거를 찾지 못했습니다."

        lines = [f"'{질문}' 관련 내부 지식베이스 검색 결과 (RAG, 상위 {len(docs)}건):"]
        for i, doc in enumerate(docs, 1):
            label = doc.metadata.get("label", "")
            source = doc.metadata.get("source", "")
            lines.append(f"[근거 {i}] {source} - {label}")
            lines.append(doc.page_content)
        return "\n".join(lines)

    return [search_internal_knowledge]


def _build_external_tools():
    from langchain_core.tools import tool
    from langchain_tavily import TavilySearch

    news_search = TavilySearch(
        max_results=3,
        topic="news",
        include_answer=True,
        include_raw_content=False,
        include_images=False,
        search_depth="advanced",
        include_domains=SUPPLEMENT_NEWS_DOMAINS,
    )
    recall_search = TavilySearch(
        max_results=3,
        topic="general",
        include_answer=True,
        include_raw_content=False,
        include_images=False,
        search_depth="advanced",
        include_domains=RECALL_ALERT_DOMAINS,
    )

    @tool
    def search_supplement_news(topic: str) -> str:
        """특정 성분·제품과 관련된 최신 뉴스·이슈를 검색합니다 (예: '루테인', '프로바이오틱스')."""
        try:
            result = news_search.invoke(f"{topic} 최신 뉴스")
        except Exception as exc:  # Tool 호출 실패(API 오류·타임아웃)
            return f"지금은 최신 정보를 가져오지 못했습니다 (오류: {exc}). 내부 DB 근거로만 답변해 주세요."

        if not isinstance(result, dict):
            return f"지금은 최신 정보를 가져오지 못했습니다 (오류: {result}). 내부 DB 근거로만 답변해 주세요."

        items = result.get("results") or []
        if not items:
            return f"'{topic}'에 대한 최신 뉴스를 찾지 못했습니다."

        lines = [f"'{topic}' 관련 최신 뉴스 (최대 3건):"]
        for i, item in enumerate(items[:3], 1):
            title = item.get("title", "제목 없음")
            content = (item.get("content") or "")[:150]
            url = item.get("url", "")
            lines.append(f"{i}. {title}\n   {content}...\n   출처: {url}")
        return "\n".join(lines)

    @tool
    def search_recall_alert(product_name: str) -> str:
        """특정 건강기능식품의 회수·판매중지·부작용 경보를 검색합니다."""
        try:
            result = recall_search.invoke(f"{product_name} 회수 판매중지 위해상품 경보")
        except Exception as exc:
            return f"지금은 회수·경보 정보를 가져오지 못했습니다 (오류: {exc}). 내부 DB 근거로만 답변해 주세요."

        if not isinstance(result, dict):
            return f"지금은 회수·경보 정보를 가져오지 못했습니다 (오류: {result}). 내부 DB 근거로만 답변해 주세요."

        items = result.get("results") or []
        if not items:
            return f"'{product_name}'에 대한 회수·경보 정보를 찾지 못했습니다. 발견된 회수·판매중지 이력이 없습니다."

        lines = [f"'{product_name}' 회수·안전성 경보 검색 결과 (최대 3건):"]
        for i, item in enumerate(items[:3], 1):
            title = item.get("title", "제목 없음")
            content = (item.get("content") or "")[:150]
            url = item.get("url", "")
            lines.append(f"{i}. {title}\n   {content}...\n   출처: {url}")
        lines.append("※ 회수·경보 관련 내용이 발견되었습니다. 사용자에게 CS 상담 연결을 반드시 안내하세요.")
        lines.append(_RECALL_FOUND_MARKER)
        return "\n".join(lines)

    return [search_supplement_news, search_recall_alert]


_agent = None


def _get_agent():
    """Agent는 API 키 확인 후 최초 1회만 만들어 재사용한다."""
    global _agent
    if _agent is None:
        from langchain.agents import create_agent
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.1,
            max_tokens=2000,
        )
        tools = _build_internal_tools() + _build_external_tools()
        _agent = create_agent(model=llm, tools=tools, system_prompt=_SYSTEM_PROMPT)
    return _agent


def ask(message: str, history: list[ChatMessage]) -> ChatResponse:
    """사용자 메시지 하나에 대해 Agent를 실행하고, 답변·출처·CS 상담 권장 여부를 반환한다."""
    _require_config()

    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    messages = []
    for turn in history:
        if turn.role == "user":
            messages.append(HumanMessage(content=turn.content))
        else:
            messages.append(AIMessage(content=turn.content))
    messages.append(HumanMessage(content=message))

    try:
        # RF-4 운영/비용 계측: 이 블록 안에서 일어나는 모든 LLM 호출(Tool 호출
        # 루프 포함)의 토큰 사용량을 자동 합산해 llm_usage_log에 기록한다.
        with usage_service.track_usage(feature="chat") as usage:
            agent = _get_agent()
            result = agent.invoke({"messages": messages})
            usage.tool_call_count = sum(
                1 for m in result["messages"] if isinstance(m, ToolMessage)
            )
    except AgentNotConfiguredError:
        raise
    except Exception as exc:  # LLM/네트워크 연결 실패 등
        raise AgentError(f"AI 상담 응답을 생성하지 못했습니다: {exc}") from exc

    result_messages = result["messages"]
    answer = result_messages[-1].content.replace(_RECALL_FOUND_MARKER, "").strip()

    references: list[str] = []
    sources: list[str] = []
    cs_recommended = False
    for msg in result_messages:
        if isinstance(msg, ToolMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            for label in _REFERENCE_LABEL_PATTERN.findall(content):
                if label not in references:
                    references.append(label)
            for url in _URL_PATTERN.findall(content):
                if url not in sources:
                    sources.append(url)
            if _RECALL_FOUND_MARKER in content:
                cs_recommended = True

    return ChatResponse(
        answer=answer,
        참고_문서_목록=references[:5],
        출처_URL_목록=sources[:5],
        cs_상담_권장=cs_recommended,
    )
