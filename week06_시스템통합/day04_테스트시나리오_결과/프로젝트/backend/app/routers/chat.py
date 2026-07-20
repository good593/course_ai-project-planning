"""RF-3 AI상담 API — Tool을 사용하는 AI Agent(내부 DB + 외부 인터넷 조회)."""
from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import agent_service

router = APIRouter(prefix="/chat", tags=["RF-3 AI상담 (Agent)"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    """사용자 메시지에 대해 내부 DB를 우선 조회하고, 부족하면 외부 Tool(뉴스/회수경보)을 호출해 답한다."""
    try:
        return agent_service.ask(request.message, request.history)
    except agent_service.AgentNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except agent_service.AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
