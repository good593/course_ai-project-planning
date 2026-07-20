"""상품 조회 관련 응답 스키마."""
from pydantic import BaseModel, ConfigDict


class ProductSummary(BaseModel):
    """목록/추천 결과에서 사용하는 간략 정보."""

    model_config = ConfigDict(from_attributes=True)

    상품ID: str
    상품명: str
    업소명: str
    카테고리: str
    관련_증상: str


class ProductDetail(ProductSummary):
    """상세페이지에서 사용하는 전체 정보."""

    검색키워드: str
    신고번호: str | None = None
    등록일자: str | None = None
    소비기한: str | None = None
    성상: str | None = None
    섭취량_섭취방법: str | None = None
    섭취시주의사항: str | None = None
    기능성_내용: str | None = None
    신고번호_상세조회URL: str | None = None
    데이터출처: str | None = None
