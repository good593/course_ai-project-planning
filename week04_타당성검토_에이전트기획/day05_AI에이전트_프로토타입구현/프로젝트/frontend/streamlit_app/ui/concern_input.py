"""건강고민 입력 (UI-W-002) — day03 와이어프레임_디스크립션/UI-W-002 참고."""
import streamlit as st

from config import HEALTH_CONCERNS
from state import go


def render() -> None:
    if st.button("← 뒤로", key="input_back"):
        go("home")
    st.progress(0.5, text="1 / 2 단계")

    st.subheader("건강 고민을 선택하세요")
    concerns = st.multiselect(
        "건강 고민을 선택하세요 (다중 선택 가능)",
        options=HEALTH_CONCERNS,
        default=st.session_state.selected_concerns,
        label_visibility="collapsed",
    )
    st.session_state.selected_concerns = concerns
    if len(concerns) > 1:
        st.caption(f"여러 개를 선택하면 가장 먼저 고른 '{concerns[0]}'를 기준으로 추천해드려요.")

    with st.expander("알레르기 · 복용 중인 제품 입력 (선택)"):
        st.session_state.allergy_note = st.text_area(
            "알레르기 성분이나 복용 중인 제품을 적어주세요",
            value=st.session_state.allergy_note,
            placeholder="예: 갑각류 알레르기, 오메가3 복용 중",
        )
        st.caption("Should 범위 정보로, 이번 MVP 추천 로직에는 아직 반영되지 않고 참고용으로만 저장돼요.")

    # day04 예외 흐름 1. 필수 정보 누락 — 채워야 진행할 수 있는 것을 알려준다.
    if not concerns:
        st.info("건강 고민을 1개 이상 선택해 주세요.")

    if st.button("맞춤 추천 받기 →", type="primary", disabled=not concerns):
        st.session_state.offset = 0
        go("result")
