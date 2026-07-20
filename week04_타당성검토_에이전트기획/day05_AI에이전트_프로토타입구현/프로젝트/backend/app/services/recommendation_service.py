"""RF-1 AI 맞춤 상품 추천 로직 (규칙 기반 매칭).

'AI 맞춤 추천'이라 부르지만 실제로는 LLM을 쓰지 않고,
'상품.관련_증상'과 '영양소_기능성.관련_증상'을 매칭해 추천하는 규칙 기반 로직이다.
"""
from sqlalchemy.orm import Session

from app.core.config import RECOMMENDATION_PAGE_SIZE
from app.models.nutrient import NutrientFunction
from app.models.product import Product
from app.schemas.product import ProductSummary
from app.schemas.recommendation import (
    RecommendationItem,
    RecommendationReason,
    RecommendationResponse,
)


def _build_reasons(db: Session, product: Product, 건강고민: str) -> list[RecommendationReason]:
    """RF-1.3 추천 근거 표시: 상품의 주요원료가 왜 이 건강고민에 도움이 되는지 근거를 붙인다."""
    functions = (
        db.query(NutrientFunction)
        .filter(
            NutrientFunction.영양소 == product.검색키워드,
            NutrientFunction.관련_증상.like(f"%{건강고민}%"),
        )
        .all()
    )
    if not functions:
        # 증상 표현이 정확히 일치하지 않을 경우, 해당 원료의 기능성 전체를 근거로 대체 제공한다.
        functions = (
            db.query(NutrientFunction).filter(NutrientFunction.영양소 == product.검색키워드).all()
        )
    return [
        RecommendationReason(
            영양소=f.영양소, 기능성=f.기능성, 근거_설명=f.근거_설명, 출처=f.출처
        )
        for f in functions
    ]


def recommend_products(
    db: Session, 건강고민: str, offset: int = 0
) -> RecommendationResponse:
    """RF-1.1~1.4: 건강고민을 입력받아 최대 5개씩 맞춤 상품을 추천한다.

    offset을 늘려 호출하면 RF-1.4(재추천 요청)로 다음 5개를 이어서 보여준다.
    """
    matched = (
        db.query(Product)
        .filter(Product.관련_증상.like(f"%{건강고민}%"))
        .order_by(Product.상품ID)
    )
    전체_매칭_건수 = matched.count()
    page = matched.offset(offset).limit(RECOMMENDATION_PAGE_SIZE).all()

    추천상품 = [
        RecommendationItem(
            상품=ProductSummary.model_validate(product),
            추천근거=_build_reasons(db, product, 건강고민),
        )
        for product in page
    ]

    다음_offset = offset + RECOMMENDATION_PAGE_SIZE
    다음_재추천_offset = 다음_offset if 다음_offset < 전체_매칭_건수 else None

    return RecommendationResponse(
        건강고민=건강고민,
        전체_매칭_건수=전체_매칭_건수,
        추천상품=추천상품,
        다음_재추천_offset=다음_재추천_offset,
    )
