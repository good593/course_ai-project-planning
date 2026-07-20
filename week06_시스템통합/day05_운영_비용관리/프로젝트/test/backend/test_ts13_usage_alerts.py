# -*- coding: utf-8 -*-
"""TS-13: 비용·토큰·오류율 알림 기준을 넘으면 알림이 발생한다.

관련 API: GET /usage/alerts
관련 모듈: app/services/usage_service.py (get_alerts)

"AI 서비스 운영 및 비용 관리.md"의 '알림 기준이 필요한 이유' 표(비용 급증/
Token 급증/오류 증가)를 그대로 검증한다. 임계값은 monkeypatch로 낮추거나
높여서 판정 로직만 결정적으로 확인하고, 오늘 날짜에 기록을 남기므로 테스트
후 usage_log_cleanup으로 정리한다.
"""
from app.core.database import SessionLocal
from app.services import usage_service


def test_cost_alert_triggers_when_threshold_exceeded(usage_log_cleanup, monkeypatch):
    """오늘 누적 비용이 DAILY_COST_ALERT_USD를 넘으면 '비용 급증' 알림이 발생한다."""
    # 토큰/오류율 알림은 이 테스트와 무관하게 절대 발동하지 않도록 기준을 아주 높여 둔다.
    monkeypatch.setattr(usage_service, "TOKEN_SPIKE_RATIO", 1_000_000)
    monkeypatch.setattr(usage_service, "ERROR_RATE_ALERT", 1.0)
    monkeypatch.setattr(usage_service, "DAILY_COST_ALERT_USD", 0.0)

    usage_service.record_usage(
        feature="chat", model="openai/gpt-oss-120b",
        input_tokens=10_000, output_tokens=2_000, success=True,
    )

    db = SessionLocal()
    try:
        alerts = usage_service.get_alerts(db)
    finally:
        db.close()

    cost_alerts = [a for a in alerts if a.기준 == "비용 급증"]
    assert cost_alerts, "비용이 임계값(0.0)을 초과했는데 '비용 급증' 알림이 없습니다."
    assert cost_alerts[0].현재값 > 0.0


def test_no_alerts_when_thresholds_not_exceeded(usage_log_cleanup, monkeypatch):
    """모든 임계값을 충분히 높게 잡으면 어떤 데이터가 있어도 알림이 발생하지 않는다."""
    monkeypatch.setattr(usage_service, "DAILY_COST_ALERT_USD", 1_000_000.0)
    monkeypatch.setattr(usage_service, "TOKEN_SPIKE_RATIO", 1_000_000)
    monkeypatch.setattr(usage_service, "ERROR_RATE_ALERT", 1.0)

    usage_service.record_usage(
        feature="chat", model="openai/gpt-oss-120b",
        input_tokens=100, output_tokens=20, success=False, error_message="테스트 실패",
    )

    db = SessionLocal()
    try:
        alerts = usage_service.get_alerts(db)
    finally:
        db.close()

    assert alerts == []


def test_error_rate_alert_triggers_on_high_failure_rate(usage_log_cleanup, monkeypatch):
    """오늘 호출 실패율이 ERROR_RATE_ALERT를 넘으면 '오류 증가' 알림이 발생한다."""
    monkeypatch.setattr(usage_service, "DAILY_COST_ALERT_USD", 1_000_000.0)
    monkeypatch.setattr(usage_service, "TOKEN_SPIKE_RATIO", 1_000_000)
    monkeypatch.setattr(usage_service, "ERROR_RATE_ALERT", 0.01)  # 1%만 넘어도 알림

    for _ in range(5):
        usage_service.record_usage(
            feature="chat", model="openai/gpt-oss-120b",
            input_tokens=10, output_tokens=5, success=False, error_message="테스트 실패",
        )

    db = SessionLocal()
    try:
        alerts = usage_service.get_alerts(db)
    finally:
        db.close()

    error_alerts = [a for a in alerts if a.기준 == "오류 증가"]
    assert error_alerts, "실패율이 임계값(1%)을 크게 초과했는데 '오류 증가' 알림이 없습니다."


def test_usage_alerts_endpoint_returns_expected_shape(client):
    """GET /usage/alerts가 200과 함께 예상한 필드 구조를 반환한다."""
    response = client.get("/usage/alerts")
    assert response.status_code == 200

    data = response.json()
    assert "알림_목록" in data
    assert isinstance(data["알림_목록"], list)
    for alert in data["알림_목록"]:
        assert {"기준", "설명", "현재값", "임계값"} <= alert.keys()
