"""RF-3 AI상담(Agent) 요청/응답 스키마.

week04 day04 설계문서의 Workflow를 그대로 따른다:
내부 DB 우선 → 부족하면 외부 Tool(뉴스/회수경보) 호출 → 출처 URL과 함께 답변.
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
    출처_URL_목록: list[str] = []
    # 회수·부작용 경보가 발견된 경우: 자동 연결은 금지하고, 버튼만 노출한다(Human-in-the-loop).
    cs_상담_권장: bool = False
