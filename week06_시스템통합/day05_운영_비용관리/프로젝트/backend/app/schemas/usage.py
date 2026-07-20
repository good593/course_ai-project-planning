"""RF-4 운영 대시보드(토큰 사용량/비용) 응답 스키마."""
from pydantic import BaseModel


class DailyUsage(BaseModel):
    """하루 단위로 집계한 사용량/비용 요약 한 줄."""

    날짜: str  # YYYY-MM-DD
    호출_수: int
    성공_수: int
    실패_수: int
    입력_토큰: int
    출력_토큰: int
    총_토큰: int
    총_비용_USD: float
    평균_응답시간_ms: float


class UsageSummary(BaseModel):
    조회_일수: int
    일별_사용량: list[DailyUsage]
    누적_호출_수: int
    누적_비용_USD: float
    누적_실패율: float


class UsageAlert(BaseModel):
    기준: str
    설명: str
    현재값: float
    임계값: float


class UsageAlertResponse(BaseModel):
    알림_목록: list[UsageAlert]
