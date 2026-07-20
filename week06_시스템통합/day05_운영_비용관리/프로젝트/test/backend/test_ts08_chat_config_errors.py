# -*- coding: utf-8 -*-
"""TS-08: AI상담 관련 설정이 준비되지 않았을 때 오류를 명확히 안내한다.

관련 API: POST /chat
대상 TC: TC-016, TC-017, TC-018

이 파일의 테스트는 monkeypatch로 실패 상황(키 미설정/Ollama 미실행/외부 Tool 오류)을
직접 만들어내므로, 실제 GROQ/Tavily 호출이나 Ollama 실행 없이도 항상 결정적으로
동작한다(비용 발생 없음, RUN_LIVE_AI_TESTS 불필요).
"""
from app.services import agent_service, rag_service


def test_tc016_chat_returns_503_when_api_keys_missing(client, monkeypatch):
    """TC-016: GROQ/TAVILY API 키 미설정 시 503과 안내 메시지를 반환한다."""
    monkeypatch.setattr(agent_service, "GROQ_API_KEY", "")
    monkeypatch.setattr(agent_service, "TAVILY_API_KEY", "")

    response = client.post("/chat", json={"message": "루테인이 뭐야?", "history": []})

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "GROQ_API_KEY" in detail
    assert "TAVILY_API_KEY" in detail


def test_tc017_internal_knowledge_tool_survives_ollama_down(monkeypatch):
    """TC-017: Ollama 미실행 상태에서 search_internal_knowledge가 예외 대신
    안내 문구를 반환하는지 확인한다(서버 500으로 죽지 않아야 함).
    """

    def raise_not_ready(query: str, k: int):
        raise rag_service.RagNotReadyError(
            "내부 지식베이스 벡터 검색을 사용할 수 없습니다. 로컬 Ollama 서버(ollama serve)와 "
            "임베딩 모델이 준비되었는지 확인해주세요."
        )

    monkeypatch.setattr(rag_service, "search", raise_not_ready)

    tools = agent_service._build_internal_tools()
    search_internal_knowledge = tools[0]

    # 예외가 그대로 전파되면(=서버가 500으로 죽으면) 이 줄에서 테스트가 실패한다.
    result = search_internal_knowledge.invoke({"질문": "루테인이 어떤 성분이야?"})

    assert isinstance(result, str)
    assert "Ollama" in result


def test_tc018_supplement_news_tool_handles_tavily_failure(monkeypatch):
    """TC-018: 외부 뉴스 검색 Tool이 실패해도 원문 에러가 아닌 안내 문구로 감싸서 반환한다."""
    from langchain_tavily import TavilySearch

    def raise_timeout(self, *args, **kwargs):
        raise TimeoutError("네트워크 연결에 실패했습니다.")

    monkeypatch.setattr(TavilySearch, "invoke", raise_timeout)

    tools = agent_service._build_external_tools()
    search_supplement_news = next(t for t in tools if t.name == "search_supplement_news")

    result = search_supplement_news.invoke({"topic": "루테인"})

    assert result.startswith("지금은 최신 정보를 가져오지 못했습니다")
