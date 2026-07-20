"""RF-4 AI 서비스 운영 대시보드 API — 토큰 사용량/비용 집계·알림."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.usage import UsageAlertResponse, UsageSummary
from app.services import usage_service

router = APIRouter(prefix="/usage", tags=["RF-4 운영 대시보드 (토큰/비용)"])


@router.get("/summary", response_model=UsageSummary)
def read_usage_summary(days: int = 14, db: Session = Depends(get_db)):
    """최근 N일간 일별 호출 수·토큰·비용·평균 응답시간·실패율을 집계해 반환한다."""
    return usage_service.get_summary(db, days=days)


@router.get("/alerts", response_model=UsageAlertResponse)
def read_usage_alerts(db: Session = Depends(get_db)):
    """비용 급증 / 토큰 급증 / 오류 증가 등 운영 알림 기준 초과 여부를 반환한다."""
    return UsageAlertResponse(알림_목록=usage_service.get_alerts(db))
