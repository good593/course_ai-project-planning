"""여러 화면에서 재사용하는 작은 UI 조각들.

day03 화면설계서(메뉴트리)의 사이드바 내비게이션과, day04 예외 처리 흐름의
오류 메시지 표시 방식을 공통 함수로 뽑아둔 것이다.
"""
import streamlit as st

import api_client
from state import go

# day03 메뉴트리와 동일한 순서/구분(Must·Should·Could·Won't).
_NAV_ITEMS = [
    ("home", "홈", True),
    ("input", "건강고민입력", True),
    ("result", "추천결과", True),
    ("detail", "상품상세", True),
    ("chat", "AI상담(고객센터)", False),  # Could, RF-3.0 — backend 미구현
]


def render_sidebar(current_page: str) -> None:
    with st.sidebar:
        st.markdown("### 🥗 건강한하루")
        st.caption("AI 맞춤 영양제 추천")

        backend_ok = api_client.health_check()
        status = "🟢 백엔드 연결됨" if backend_ok else "🔴 백엔드 연결 안 됨"
        st.caption(status)
        if not backend_ok:
            st.caption("backend/ 폴더에서 uvicorn 서버를 먼저 실행해 주세요.")

        st.divider()
        for key, label, implemented in _NAV_ITEMS:
            suffix = "" if implemented else " (준비중)"
            button_type = "primary" if key == current_page else "secondary"
            if st.button(f"{label}{suffix}", key=f"nav_{key}", type=button_type,
                         use_container_width=True):
                go(key)

        st.divider()
        st.caption("마이페이지 — MVP 이후 제공 (Won't have)")


def warning_banner(text: str, level: str = "warning") -> None:
    if level == "error":
        st.error(f"⛔ {text}")
    else:
        st.warning(f"⚠️ {text}")


def empty_state(message: str, button_label: str, on_click_page: str, **updates) -> None:
    """day04 예외 흐름 2. 추천 결과 없음"""
    st.info(f"🗂️ {message}")
    if st.button(button_label, type="primary"):
        go(on_click_page, **updates)


def api_error_banner(exc: api_client.ApiError) -> None:
    """day04 오류 메시지 표: 상황 설명 + 다음 행동이 함께 보이도록 한다."""
    st.error(exc.message)
    if isinstance(exc, api_client.ApiConnectionError):
        st.caption("잠시 후 페이지를 새로고침하거나 다시 시도해 주세요.")
