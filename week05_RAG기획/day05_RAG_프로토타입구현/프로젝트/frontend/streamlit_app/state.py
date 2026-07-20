"""st.session_state 초기화와 화면 전환(go)을 한곳에 모아둔다.

day02 User Flow의 화면 이동을, day03 Screen ID를 key로 하는
간단한 상태 머신(st.session_state["page"])으로 옮긴 것이다.
"""
import streamlit as st

_DEFAULTS = {
    "page": "home",              # home / input / result / detail / chat
    "selected_concerns": [],      # 건강고민입력(UI-W-002)에서 선택한 고민 목록
    "allergy_note": "",           # 알레르기 · 복용 중인 제품(Should, 참고용)
    "offset": 0,                  # RF-1.4 재추천 offset
    "selected_product_id": None,  # 상품상세(UI-H-004)로 넘길 상품ID
    "age_group": "19~29세",
    "gender": "여성",
    "chat_messages": [],          # RF-3 AI상담 대화 이력: [{"role": "user"|"assistant", "content": str}]
}


def init_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(page: str, **updates) -> None:
    """다른 화면으로 이동하면서 필요한 session_state 값을 함께 갱신한다."""
    st.session_state["page"] = page
    for key, value in updates.items():
        st.session_state[key] = value
    st.rerun()
