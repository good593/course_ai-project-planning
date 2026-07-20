"""RF-3 AI상담(Agent) 요청/응답 스키마.

week04 day04 설계문서의 Workflow를 week05 RAG로 확장한 형태를 따른다:
내부 지식베이스(RAG 벡터검색) 우선 → 부족하면 외부 Tool(뉴스/회수경보) 호출
→ 근거 문서(내부)와 출처 URL(외부)을 함께 답변.
"""
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """프론트엔드가 보관하는 대화 이력 한 줄."""

    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    # RF-3.3 근거 문서 인용: 내부 지식베이스(RAG 벡터검색)에서 찾은 근거 문서 라벨.
    참고_문서_목록: list[str] = []
    # 외부 Tool(뉴스/회수경보) 검색으로 찾은 출처 URL.
    출처_URL_목록: list[str] = []
    # 회수·부작용 경보가 발견된 경우: 자동 연결은 금지하고, 버튼만 노출한다(Human-in-the-loop).
    cs_상담_권장: bool = False
