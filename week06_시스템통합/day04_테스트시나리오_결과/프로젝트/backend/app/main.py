"""건강한하루 FastAPI 진입점.

라우터를 조립하기만 하고, 실제 로직은 routers/services 모듈에 위임한다.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, GROQ_API_KEY, TAVILY_API_KEY
from app.routers import chat, dosage, nutrients, products, recommendations
from app.services import agent_service, rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """RF-3 Agent/RAG는 첫 요청에서 지연 생성되면 프론트 타임아웃(8초)을 넘기기
    쉬우므로, 서버 시작 시 벡터스토어와 Agent를 미리 만들어 둔다."""
    if GROQ_API_KEY and TAVILY_API_KEY:
        try:
            rag_service._get_vectorstore()
            agent_service._get_agent()
        except Exception:
            # 워밍업 실패는 무시한다. 실제 /chat 요청에서 다시 시도되고,
            # 필요하면 그때 에러가 사용자에게 안내된다.
            pass
    yield


app = FastAPI(
    title=APP_TITLE, description=APP_DESCRIPTION, version=APP_VERSION, lifespan=lifespan
)

app.include_router(products.router)
app.include_router(recommendations.router)
app.include_router(nutrients.router)
app.include_router(dosage.router)
app.include_router(chat.router)


@app.get("/", tags=["헬스체크"])
def health_check():
    return {"status": "ok", "service": APP_TITLE}
