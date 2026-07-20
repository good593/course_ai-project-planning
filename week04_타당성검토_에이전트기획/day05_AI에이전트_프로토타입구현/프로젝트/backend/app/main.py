"""건강한하루 FastAPI 진입점.

라우터를 조립하기만 하고, 실제 로직은 routers/services 모듈에 위임한다.
"""
from fastapi import FastAPI

from app.core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from app.routers import chat, dosage, nutrients, products, recommendations

app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, version=APP_VERSION)

app.include_router(products.router)
app.include_router(recommendations.router)
app.include_router(nutrients.router)
app.include_router(dosage.router)
app.include_router(chat.router)


@app.get("/", tags=["헬스체크"])
def health_check():
    return {"status": "ok", "service": APP_TITLE}
