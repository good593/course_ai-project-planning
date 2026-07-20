"""RF-1 AI 맞춤 상품 추천 요청/응답 스키마."""
from pydantic import BaseModel, Field

from app.schemas.product import ProductSummary


class RecommendationRequest(BaseModel):
    """RF-1.1 건강고민 입력 / RF-1.4 재추천 요청.

    같은 건강고민으로 재추천을 요청할 때는 offset을 늘려서
    이전에 보여준 상품을 건너뛰도록 한다.
    """

    건강고민: str = Field(..., min_length=1, description="예: 피로, 눈 건강, 장 건강")
    offset: int = Field(0, ge=0, description="재추천 시 건너뛸 이전 추천 개수")


class RecommendationReason(BaseModel):
    """RF-1.3 추천 근거 표시: 추천에 사용된 영양소·기능성 정보."""

    영양소: str
    기능성: str
    근거_설명: str | None = None
    출처: str | None = None


class RecommendationItem(BaseModel):
    상품: ProductSummary
    추천근거: list[RecommendationReason]


class RecommendationResponse(BaseModel):
    건강고민: str
    전체_매칭_건수: int
    추천상품: list[RecommendationItem]
    다음_재추천_offset: int | None = Field(
        None, description="다음 재추천 요청 시 사용할 offset. 더 이상 없으면 null"
    )
