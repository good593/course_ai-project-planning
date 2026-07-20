"""RF-4 LLM 호출 1건마다 남기는 토큰 사용량/비용 로그 테이블.

day04까지 만든 상품/영양소 테이블은 이미 만들어진 SQLite DB를 그대로 읽기만
했지만, 이 테이블은 day05에서 새로 쓰기 시작하는 테이블이라 애플리케이션이
직접 만들어야 한다. 그래서 이 모듈을 import하는 시점에 테이블이 없으면
자동으로 만들어 둔다(이미 있으면 아무 일도 하지 않는다).
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, engine


def _utcnow() -> datetime:
    """타임존 정보 없는 UTC 시각. usage_service의 집계 쿼리와 비교 기준을 맞추기 위해 naive로 통일한다."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UsageLog(Base):
    __tablename__ = "llm_usage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    feature: Mapped[str] = mapped_column(String, default="chat")
    model: Mapped[str] = mapped_column(String)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)

    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)


# 다른 테이블(상품/영양소 등)과 달리 llm_usage_log는 애플리케이션이 소유한 테이블이므로,
# 이 모델을 import하기만 해도 테이블이 준비되도록 해 둔다(checkfirst=True가 기본값이라
# 이미 있으면 건드리지 않는다).
Base.metadata.create_all(bind=engine, tables=[UsageLog.__table__])
