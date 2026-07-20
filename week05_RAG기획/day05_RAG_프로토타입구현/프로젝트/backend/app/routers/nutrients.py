"""RF-2 AI 성분 설명 API (사전 조회형, LLM 미사용)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.nutrient import NutrientExplanation
from app.services import nutrient_service

router = APIRouter(prefix="/nutrients", tags=["AI 성분 설명"])


@router.get("/{nutrient_name}", response_model=NutrientExplanation)
def read_nutrient_explanation(nutrient_name: str, db: Session = Depends(get_db)):
    """RF-2.1 성분 용어 쉬운 설명 + RF-2.2 근거 출처 표기.

    경로 파라미터 이름은 영문(nutrient_name)으로 둔다. Starlette이 경로 파라미터를
    ASCII 식별자로만 인식하므로 {영양소}처럼 한글을 쓰면 매칭되지 않는다.
    """
    explanation = nutrient_service.get_nutrient_explanation(db, nutrient_name)
    if explanation is None:
        raise HTTPException(status_code=404, detail="해당 영양소 정보를 찾을 수 없습니다.")
    return explanation
