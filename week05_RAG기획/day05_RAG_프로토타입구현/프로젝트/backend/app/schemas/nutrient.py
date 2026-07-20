"""영양소 성분 설명(RF-2) / 섭취기준(RF-4) 응답 스키마."""
from pydantic import BaseModel, ConfigDict


class NutrientFunctionOut(BaseModel):
    """RF-2.1/2.2: 영양소 하나에 대한 쉬운 설명 + 근거 출처."""

    model_config = ConfigDict(from_attributes=True)

    영양소: str
    분류: str | None = None
    기능성: str
    관련_증상: str | None = None
    근거_설명: str | None = None
    신뢰도: str | None = None
    출처: str | None = None
    출처_URL: str | None = None


class NutrientExplanation(BaseModel):
    """하나의 영양소에 대해 여러 기능성 근거를 묶어서 보여주는 응답."""

    영양소: str
    기능성_목록: list[NutrientFunctionOut]


class IntakeStandardOut(BaseModel):
    """RF-4.1: 권장/상한 섭취량 표시."""

    model_config = ConfigDict(from_attributes=True)

    영양소: str
    연령대: str | None = None
    성별: str | None = None
    임신여부: str | None = None
    수유여부: str | None = None
    권장섭취량: str | None = None
    충분섭취량: str | None = None
    상한섭취량: str | None = None
    단위: str | None = None
    출처: str | None = None
    기관: str | None = None
