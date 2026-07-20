"""홈 (UI-W-001) — day03 와이어프레임_디스크립션/UI-W-001_홈 참고."""
import streamlit as st

from config import HOME_QUICK_CONCERNS
from state import go


def render() -> None:
    st.title("오늘도 건강한하루 🌿")
    st.caption("건강 고민을 알려주시면 AI가 근거와 함께 맞춤 상품을 추천해드려요.")

    if st.button("건강고민 시작하기 →", type="primary"):
        go("input")

    st.write("")
    st.subheader("자주 찾는 고민")
    cols = st.columns(len(HOME_QUICK_CONCERNS))
    for col, concern in zip(cols, HOME_QUICK_CONCERNS):
        if col.button(concern, key=f"home_chip_{concern}", use_container_width=True):
            # 카테고리 칩 클릭 시 해당 고민이 선택된 상태로 건강고민입력 화면에 진입한다.
            go("input", selected_concerns=[concern])
