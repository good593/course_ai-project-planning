# -*- coding: utf-8 -*-
"""TS-12: 일별 토큰/비용 사용량이 정확히 집계된다.

관련 API: GET /usage/summary
관련 모듈: app/services/usage_service.py (get_daily_usage, get_summary)

날짜별 SQL 집계(get_daily_usage)는 실제 DB에 기록을 남기고 검증하되, 실제
운영 데이터와 절대 겹치지 않는 과거 날짜(2020-01-01)를 써서 기존 기록에
영향을 주거나 받지 않게 한다. 누적 합산 로직(get_summary)은 get_daily_usage를
monkeypatch해 고정된 값으로 순수하게 계산만 검증한다(DB 접근 없음).
"""
from datetime import datetime

from app.core.database import SessionLocal
from app.schemas.usage import DailyUsage
from app.services import usage_service

_ISOLATED_DATE = datetime(2020, 1, 1)  # 실제 서비스 트래픽과 절대 겹치지 않는 날짜.


def test_get_daily_usage_groups_and_sums_by_date(usage_log_cleanup):
    """같은 날짜에 기록된 여러 호출이 하나의 일별 행으로 합산된다."""
    usage_service.record_usage(
        feature="chat", model="test-model-ts12", input_tokens=100, output_tokens=20,
        latency_ms=500, success=True, created_at=_ISOLATED_DATE.replace(hour=9),
    )
    usage_service.record_usage(
        feature="chat", model="test-model-ts12", input_tokens=50, output_tokens=10,
        latency_ms=300, success=False, error_message="테스트 실패", created_at=_ISOLATED_DATE.replace(hour=15),
    )

    db = SessionLocal()
    try:
        daily = usage_service.get_daily_usage(db, days=3650)
    finally:
        db.close()

    row = next((d for d in daily if d.날짜 == "2020-01-01"), None)
    assert row is not None, "2020-01-01 집계 행을 찾지 못했습니다."
    assert row.호출_수 == 2
    assert row.성공_수 == 1
    assert row.실패_수 == 1
    assert row.입력_토큰 == 150
    assert row.출력_토큰 == 30
    assert row.총_토큰 == 180
    assert row.평균_응답시간_ms == 400.0


def test_get_summary_aggregates_daily_rows(monkeypatch):
    """get_summary는 get_daily_usage가 반환한 일별 값을 더하기만 한다(순수 계산, DB 미접근)."""
    fake_daily = [
        DailyUsage(
            날짜="2020-01-01", 호출_수=3, 성공_수=2, 실패_수=1,
            입력_토큰=100, 출력_토큰=20, 총_토큰=120, 총_비용_USD=0.01, 평균_응답시간_ms=200.0,
        ),
        DailyUsage(
            날짜="2020-01-02", 호출_수=1, 성공_수=1, 실패_수=0,
            입력_토큰=10, 출력_토큰=5, 총_토큰=15, 총_비용_USD=0.001, 평균_응답시간_ms=150.0,
        ),
    ]
    monkeypatch.setattr(usage_service, "get_daily_usage", lambda db, days: fake_daily)

    summary = usage_service.get_summary(db=None, days=7)

    assert summary.누적_호출_수 == 4
    assert summary.누적_비용_USD == round(0.01 + 0.001, 6)
    assert summary.누적_실패율 == round(1 / 4, 4)


def test_usage_summary_endpoint_returns_expected_shape(client):
    """GET /usage/summary가 200과 함께 예상한 필드 구조를 반환한다(값 자체는 공유 DB라 검증 안 함)."""
    response = client.get("/usage/summary", params={"days": 7})
    assert response.status_code == 200

    data = response.json()
    assert data["조회_일수"] == 7
    assert isinstance(data["일별_사용량"], list)
    assert isinstance(data["누적_호출_수"], int)
    assert isinstance(data["누적_비용_USD"], (int, float))
