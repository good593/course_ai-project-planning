"""RF-4 토큰 사용량/비용 자동 계측 서비스.

"AI 서비스 운영 및 비용 관리.md" 강의의 세 가지 축을 그대로 구현한다.
  1) 계측: LLM 호출 1건마다 입력/출력 토큰과 비용을 자동으로 기록한다
     (agent_service.ask()가 track_usage()로 감싸기만 하면 된다).
  2) 집계: 일별 호출 수·토큰·비용·응답시간·실패율을 계산한다(get_summary).
  3) 알림: 비용 급증/토큰 급증/오류 증가 기준을 넘었는지 확인한다(get_alerts).

토큰 수집은 LangChain의 `get_usage_metadata_callback()`을 사용한다. 이 콜백은
`with` 블록 안에서 일어나는 모든 ChatModel 호출(LangGraph Agent가 Tool 호출
루프 때문에 LLM을 여러 번 부르는 경우 포함)의 `AIMessage.usage_metadata`를
모델별로 자동 합산해 준다. 즉, 각 서비스 코드에서 토큰을 직접 세지 않아도 된다.
"""
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.config import DAILY_COST_ALERT_USD, ERROR_RATE_ALERT, TOKEN_SPIKE_RATIO
from app.core.database import SessionLocal
from app.core.pricing import calc_cost_usd
from app.models.usage_log import UsageLog
from app.schemas.usage import DailyUsage, UsageAlert, UsageSummary


def _utcnow() -> datetime:
    """타임존 정보 없는 UTC 시각. SQLite DATETIME 컬럼과 비교하기 쉽도록 naive로 통일한다."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── 1) 계측 ──────────────────────────────────────────────────────────
class _UsageTracker:
    """`with usage_service.track_usage(...)` 블록 핸들.

    블록 안에서 실제 LLM 호출이 끝나면 `__exit__`에서 토큰 사용량을 모델별로
    집계해 DB에 기록한다. 블록 안에서 예외가 나도(LLM 오류 등) 실패 기록을
    남긴 뒤 예외를 그대로 다시 던진다.
    """

    def __init__(self, feature: str):
        self.feature = feature
        self.tool_call_count = 0
        self._start = 0.0
        self._callback = None
        self._cm = None

    def __enter__(self) -> "_UsageTracker":
        from langchain_core.callbacks import get_usage_metadata_callback

        self._start = time.perf_counter()
        self._cm = get_usage_metadata_callback()
        self._callback = self._cm.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        latency_ms = int((time.perf_counter() - self._start) * 1000)
        self._cm.__exit__(exc_type, exc, tb)

        success = exc is None
        error_message = str(exc)[:500] if exc is not None else None

        usage_by_model = dict(self._callback.usage_metadata or {})
        if not usage_by_model:
            # LLM이 한 번도 응답하지 못한 채 끝난 경우(연결 실패 등)에도 실패 기록은 남긴다.
            record_usage(
                feature=self.feature,
                model="unknown",
                input_tokens=0,
                output_tokens=0,
                tool_call_count=self.tool_call_count,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
            )
        else:
            for model, usage in usage_by_model.items():
                record_usage(
                    feature=self.feature,
                    model=model,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    tool_call_count=self.tool_call_count,
                    latency_ms=latency_ms,
                    success=success,
                    error_message=error_message,
                )

        return False  # 예외를 삼키지 않고 호출자에게 그대로 전파한다.


def track_usage(feature: str = "chat") -> _UsageTracker:
    """LLM 호출 1건을 감싸 토큰 사용량/비용을 자동 기록하는 컨텍스트 매니저.

    사용 예 (agent_service.ask 내부):
        with usage_service.track_usage("chat") as usage:
            result = agent.invoke({"messages": messages})
            usage.tool_call_count = sum(isinstance(m, ToolMessage) for m in result["messages"])
    """
    return _UsageTracker(feature)


def record_usage(
    *,
    feature: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    tool_call_count: int = 0,
    latency_ms: int = 0,
    success: bool = True,
    error_message: str | None = None,
    created_at: datetime | None = None,
) -> None:
    """토큰 사용량 한 건을 비용까지 계산해 DB에 남긴다.

    요청을 처리하던 DB 세션과 별개로 짧게 세션을 열고 닫는다 — 사용량 기록
    실패가 원래 요청의 트랜잭션에 영향을 주지 않도록 하기 위해서다.
    """
    cost_usd = calc_cost_usd(model, input_tokens, output_tokens)
    db = SessionLocal()
    try:
        log = UsageLog(
            feature=feature,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            tool_call_count=tool_call_count,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            success=success,
            error_message=error_message,
        )
        if created_at is not None:
            log.created_at = created_at
        db.add(log)
        db.commit()
    finally:
        db.close()


# ── 2) 집계 ──────────────────────────────────────────────────────────
def get_daily_usage(db: Session, days: int = 14) -> list[DailyUsage]:
    """최근 N일간 일별 호출 수·토큰·비용·응답시간을 SQL GROUP BY로 집계한다."""
    cutoff = _utcnow() - timedelta(days=days)
    date_expr = func.date(UsageLog.created_at)

    rows = (
        db.query(
            date_expr.label("날짜"),
            func.count(UsageLog.id).label("호출_수"),
            func.sum(case((UsageLog.success.is_(True), 1), else_=0)).label("성공_수"),
            func.sum(case((UsageLog.success.is_(False), 1), else_=0)).label("실패_수"),
            func.coalesce(func.sum(UsageLog.input_tokens), 0).label("입력_토큰"),
            func.coalesce(func.sum(UsageLog.output_tokens), 0).label("출력_토큰"),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label("총_토큰"),
            func.coalesce(func.sum(UsageLog.cost_usd), 0.0).label("총_비용_USD"),
            func.coalesce(func.avg(UsageLog.latency_ms), 0.0).label("평균_응답시간_ms"),
        )
        .filter(UsageLog.created_at >= cutoff)
        .group_by(date_expr)
        .order_by(date_expr)
        .all()
    )

    return [
        DailyUsage(
            날짜=row.날짜,
            호출_수=row.호출_수,
            성공_수=row.성공_수,
            실패_수=row.실패_수,
            입력_토큰=row.입력_토큰,
            출력_토큰=row.출력_토큰,
            총_토큰=row.총_토큰,
            총_비용_USD=round(row.총_비용_USD, 6),
            평균_응답시간_ms=round(row.평균_응답시간_ms, 1),
        )
        for row in rows
    ]


def get_summary(db: Session, days: int = 14) -> UsageSummary:
    daily = get_daily_usage(db, days=days)
    total_calls = sum(d.호출_수 for d in daily)
    total_fail = sum(d.실패_수 for d in daily)
    total_cost = sum(d.총_비용_USD for d in daily)
    fail_rate = (total_fail / total_calls) if total_calls else 0.0

    return UsageSummary(
        조회_일수=days,
        일별_사용량=daily,
        누적_호출_수=total_calls,
        누적_비용_USD=round(total_cost, 6),
        누적_실패율=round(fail_rate, 4),
    )


# ── 3) 알림 ──────────────────────────────────────────────────────────
def _aggregate(db: Session, start: datetime, end: datetime) -> tuple[int, int, int, float]:
    """[start, end) 구간의 (호출 수, 실패 수, 총 토큰, 총 비용)을 반환한다."""
    row = (
        db.query(
            func.count(UsageLog.id),
            func.coalesce(func.sum(case((UsageLog.success.is_(False), 1), else_=0)), 0),
            func.coalesce(func.sum(UsageLog.total_tokens), 0),
            func.coalesce(func.sum(UsageLog.cost_usd), 0.0),
        )
        .filter(UsageLog.created_at >= start, UsageLog.created_at < end)
        .one()
    )
    return row[0], row[1], row[2], row[3]


def get_alerts(db: Session) -> list[UsageAlert]:
    """비용 급증/토큰 급증/오류 증가 — 강의자료 '알림 기준이 필요한 이유' 표를 그대로 판정한다."""
    now = _utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())
    baseline_start = today_start - timedelta(days=7)

    today_calls, today_fail, today_tokens, today_cost = _aggregate(db, today_start, now)
    baseline_calls, _, baseline_tokens, _ = _aggregate(db, baseline_start, today_start)

    alerts: list[UsageAlert] = []

    if today_cost > DAILY_COST_ALERT_USD:
        alerts.append(
            UsageAlert(
                기준="비용 급증",
                설명="오늘 누적 비용이 알림 기준(DAILY_COST_ALERT_USD)을 초과했습니다.",
                현재값=round(today_cost, 4),
                임계값=DAILY_COST_ALERT_USD,
            )
        )

    today_avg_tokens = (today_tokens / today_calls) if today_calls else 0.0
    baseline_avg_tokens = (baseline_tokens / baseline_calls) if baseline_calls else 0.0
    if baseline_avg_tokens > 0 and today_avg_tokens > baseline_avg_tokens * TOKEN_SPIKE_RATIO:
        alerts.append(
            UsageAlert(
                기준="토큰 급증",
                설명=f"오늘 호출당 평균 토큰이 최근 7일 평균의 {TOKEN_SPIKE_RATIO}배를 초과했습니다.",
                현재값=round(today_avg_tokens, 1),
                임계값=round(baseline_avg_tokens * TOKEN_SPIKE_RATIO, 1),
            )
        )

    today_error_rate = (today_fail / today_calls) if today_calls else 0.0
    if today_calls > 0 and today_error_rate > ERROR_RATE_ALERT:
        alerts.append(
            UsageAlert(
                기준="오류 증가",
                설명="오늘 호출 실패율이 알림 기준(ERROR_RATE_ALERT)을 초과했습니다.",
                현재값=round(today_error_rate, 4),
                임계값=ERROR_RATE_ALERT,
            )
        )

    return alerts
