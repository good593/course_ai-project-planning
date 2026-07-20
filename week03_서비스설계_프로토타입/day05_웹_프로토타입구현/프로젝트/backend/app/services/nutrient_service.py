"""RF-2 AI 성분 설명 로직 (사전 조회형, LLM 미사용).

영양소 이름으로 '영양소_기능성' 테이블을 조회해 쉬운 설명과 출처를 함께 제공한다.
"""
from sqlalchemy.orm import Session

from app.models.nutrient import NutrientFunction
from app.schemas.nutrient import NutrientExplanation, NutrientFunctionOut


def get_nutrient_explanation(db: Session, 영양소: str) -> NutrientExplanation | None:
    """RF-2.1 성분 용어 쉬운 설명 + RF-2.2 근거 출처 표기."""
    functions = db.query(NutrientFunction).filter(NutrientFunction.영양소 == 영양소).all()
    if not functions:
        return None
    return NutrientExplanation(
        영양소=영양소,
        기능성_목록=[NutrientFunctionOut.model_validate(f) for f in functions],
    )
