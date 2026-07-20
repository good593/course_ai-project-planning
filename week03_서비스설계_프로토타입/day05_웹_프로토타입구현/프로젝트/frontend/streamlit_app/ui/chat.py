"""AI 상담 · RAG FAQ (UI-W-005) — Could 범위(RF-3.0), backend 미구현.

week02 day05 backend는 LLM/RAG를 쓰지 않는 규칙 기반 기능만 구현했기 때문에
(day05 프로젝트_FastAPI 구현.md 참고) 이 화면은 실제 대화 대신, day04 예외 흐름
4번(AI 응답 신뢰도 낮음 → CS 이관)을 보여주는 자리표시자로 둔다.
"""
import streamlit as st


def render() -> None:
    st.subheader("AI 상담 (RAG FAQ)")
    st.info(
        "이 기능은 Could 범위(RF-3.0)로, 이번 MVP의 backend에는 아직 구현되어 있지 않아요. "
        "MVP 검증 이후 별도 단계에서 우선순위를 다시 검토할 예정입니다."
    )

    with st.chat_message("assistant"):
        st.write(
            "죄송해요, 지금은 자유롭게 질문에 답해드릴 수 없어요. "
            "궁금한 성분이 있다면 상품상세의 '성분 쉬운 설명'을 먼저 확인해보세요."
        )

    st.chat_input("궁금한 점을 입력하세요 (준비중)", disabled=True)

    if st.button("🙋 CS 상담 연결하기"):
        st.toast("(데모) 실제 서비스에서는 CS 상담 페이지로 연결됩니다.")
