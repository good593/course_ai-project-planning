"""건강한하루 Streamlit 프론트엔드 진입점.

실행: (frontend/ 디렉터리에서) uv run streamlit run streamlit_app/app.py

화면 전환은 st.session_state["page"] 하나로 관리하는 아주 단순한 상태 머신이다.
각 화면의 실제 내용은 ui/ 아래 모듈(day03 Screen ID와 1:1로 대응)에 있다.
"""
import streamlit as st

from config import APP_ICON, APP_TITLE
from state import init_state
from ui import chat, components, concern_input, detail, home, result, usage_dashboard

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

init_state()
components.render_sidebar(st.session_state.page)

PAGES = {
    "home": home.render,          # UI-W-001
    "input": concern_input.render,  # UI-W-002
    "result": result.render,      # UI-W-003 (+ UI-H-003-1 빈 결과 안내)
    "detail": detail.render,      # UI-H-004
    "chat": chat.render,          # UI-W-005 (Could, RF-3 AI상담 Agent)
    "usage": usage_dashboard.render,  # (Should, RF-4 운영 대시보드 — 토큰/비용 자동 집계)
}

render_page = PAGES.get(st.session_state.page, home.render)
render_page()
