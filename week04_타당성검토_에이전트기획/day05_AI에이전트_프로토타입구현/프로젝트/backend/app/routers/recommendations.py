"""RF-1 AI 맞춤 상품 추천 API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["AI 맞춤 상품 추천"])


@router.post("", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest, db: Session = Depends(get_db)):
    """RF-1.1 건강고민 입력 → RF-1.2 맞춤 추천(최대 5개) → RF-1.3 추천 근거 표시.

    RF-1.4 재추천 요청은 이전 응답의 `다음_재추천_offset` 값을
    다음 요청의 `offset`으로 그대로 넘기면 된다.
    """
    return recommendation_service.recommend_products(
        db, 건강고민=request.건강고민, offset=request.offset
    )
