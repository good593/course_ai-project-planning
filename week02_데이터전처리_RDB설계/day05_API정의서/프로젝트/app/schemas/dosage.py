"""RF-4 복용 정보 안내 요청/응답 스키마."""
from pydantic import BaseModel, Field

from app.schemas.nutrient import IntakeStandardOut


class DosageQuery(BaseModel):
    """섭취기준 조회 시 사용자 조건 (연령대/성별/임신·수유 여부)."""

    연령대: str | None = None
    성별: str | None = None
    임신여부: str | None = None
    수유여부: str | None = None


class ProductDosageInfo(BaseModel):
    """상품 하나에 들어있는 주요 원료의 권장/상한 섭취량."""

    상품ID: str
    상품명: str
    주요원료: str
    섭취기준: list[IntakeStandardOut]


class OverconsumptionCheckRequest(BaseModel):
    """RF-4.2 과다섭취 경고 안내: 장바구니(여러 상품) 동시 섭취 점검."""

    상품ID_목록: list[str] = Field(..., min_length=1)
    조건: DosageQuery = Field(default_factory=DosageQuery)


class OverconsumptionWarning(BaseModel):
    """규칙 기반 경고: 동일 영양소가 여러 상품에 중복 포함된 경우."""

    영양소: str
    중복_상품수: int
    중복_상품명: list[str]
    상한섭취량: str | None = None
    단위: str | None = None
    경고_문구: str


class OverconsumptionCheckResponse(BaseModel):
    확인_상품수: int
    경고_목록: list[OverconsumptionWarning]
    안내: str
