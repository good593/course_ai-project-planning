"""운영 대시보드 (Should, RF-4) — 토큰 사용량 · 비용 자동 집계 화면.

"AI 서비스 운영 및 비용 관리.md" 강의의 '운영 지표 예시'·'알림 기준이 필요한
이유' 표를 그대로 화면으로 옮긴 것이다. backend가 AI상담(RF-3) 호출마다
자동으로 남긴 llm_usage_log를 GET /usage/summary, /usage/alerts로 가져와
보여주기만 한다 — 이 화면 자체는 계산을 하지 않는다.
"""
import streamlit as st

import api_client
from ui import components


def render() -> None:
    st.title("📊 운영 대시보드 — 토큰 사용량 · 비용")
    st.caption(
        "AI상담(RF-3) 호출마다 자동으로 기록된 토큰 사용량과 예상 비용을 집계해서 보여줍니다. "
        "실제 청구 비용이 아니라 backend/app/core/pricing.py에 등록된 단가로 계산한 예상치입니다."
    )

    days = st.slider("조회 기간(일)", min_value=1, max_value=30, value=14)

    try:
        alerts = api_client.get_usage_alerts()["알림_목록"]
        summary = api_client.get_usage_summary(days=days)
    except api_client.ApiError as exc:
        components.api_error_banner(exc)
        return

    _render_alerts(alerts)
    _render_totals(summary)
    _render_daily_table(summary["일별_사용량"])
    _render_charts(summary["일별_사용량"])


def _render_alerts(alerts: list[dict]) -> None:
    if not alerts:
        st.success("✅ 현재 알림 기준을 초과한 항목이 없습니다.")
        return

    for alert in alerts:
        components.warning_banner(
            f"[{alert['기준']}] {alert['설명']} (현재값 {alert['현재값']} / 기준값 {alert['임계값']})"
        )


def _render_totals(summary: dict) -> None:
    st.subheader(f"최근 {summary['조회_일수']}일 누적")
    col1, col2, col3 = st.columns(3)
    col1.metric("누적 호출 수", f"{summary['누적_호출_수']:,}")
    col2.metric("누적 비용(USD)", f"${summary['누적_비용_USD']:.4f}")
    col3.metric("누적 실패율", f"{summary['누적_실패율'] * 100:.1f}%")


def _render_daily_table(daily: list[dict]) -> None:
    st.subheader("일별 사용량")
    if not daily:
        st.info("🗂️ 아직 기록된 AI상담 호출이 없습니다. AI상담 화면에서 질문을 먼저 해보세요.")
        return

    st.dataframe(
        daily,
        column_order=[
            "날짜", "호출_수", "성공_수", "실패_수",
            "입력_토큰", "출력_토큰", "총_토큰", "총_비용_USD", "평균_응답시간_ms",
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_charts(daily: list[dict]) -> None:
    if not daily:
        return

    st.subheader("추이")
    cost_col, token_col = st.columns(2)
    with cost_col:
        st.caption("일별 비용(USD)")
        st.bar_chart({"날짜": [d["날짜"] for d in daily], "총_비용_USD": [d["총_비용_USD"] for d in daily]},
                     x="날짜", y="총_비용_USD")
    with token_col:
        st.caption("일별 토큰(입력/출력)")
        st.line_chart(
            {
                "날짜": [d["날짜"] for d in daily],
                "입력_토큰": [d["입력_토큰"] for d in daily],
                "출력_토큰": [d["출력_토큰"] for d in daily],
            },
            x="날짜",
            y=["입력_토큰", "출력_토큰"],
        )
