"""AI 상담 (UI-W-005) — RF-3, Tool을 사용하는 AI Agent.

week04 day04 "AI 에이전트 챗봇 설계(외부 인터넷 조회 도구)" 문서를 그대로 구현한다.
내부 DB로 답할 수 있으면 내부 DB를 우선 쓰고, 최신 뉴스·리콜·트렌드 질문은
backend의 Agent가 TavilySearch Tool을 호출해 답한다. 회수·경보가 발견되면
자동으로 CS 상담을 연결하지 않고, 사용자가 직접 누를 수 있는 버튼만 보여준다
(day04 승인 기준 표: Human-in-the-loop).
"""
import streamlit as st

import api_client
from ui import components


def render() -> None:
    st.subheader("AI 상담")
    st.caption(
        "내부 DB(상품·영양소)를 먼저 찾아보고, 최신 뉴스·리콜/회수 여부처럼 "
        "내부 DB에 없는 정보는 인터넷을 조회해서 답해드려요."
    )

    for i, turn in enumerate(st.session_state.chat_messages):
        with st.chat_message(turn["role"]):
            st.write(turn["content"])
            if turn.get("sources"):
                with st.expander("출처"):
                    for url in turn["sources"]:
                        st.markdown(f"- {url}")
            if turn.get("cs_recommended"):
                _render_cs_alert(key=f"history_{i}")

    user_input = st.chat_input("궁금한 점을 입력하세요 (예: 루테인 관련 최신 뉴스 있어?)")
    if not user_input:
        return

    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    history = [
        {"role": t["role"], "content": t["content"]} for t in st.session_state.chat_messages[:-1]
    ]

    with st.chat_message("assistant"):
        try:
            with st.spinner("답변을 준비하고 있어요..."):
                data = api_client.chat(user_input, history)
        except api_client.ApiError as exc:
            # day04 예외 흐름: Tool/Agent 호출 실패 시 CS 상담 연결을 제안한다.
            components.api_error_banner(exc)
            fallback = "지금은 답변을 가져오지 못했어요. 잠시 후 다시 시도하거나 CS 상담을 이용해 주세요."
            st.write(fallback)
            st.session_state.chat_messages.append({"role": "assistant", "content": fallback})
            if st.button("🙋 CS 상담 연결하기", key=f"cs_error_{len(st.session_state.chat_messages)}"):
                st.toast("(데모) 실제 서비스에서는 CS 상담 페이지로 연결됩니다.")
            return

        answer = data["answer"]
        sources = data.get("출처_URL_목록", [])
        cs_recommended = data.get("cs_상담_권장", False)

        st.write(answer)
        if sources:
            with st.expander("출처"):
                for url in sources:
                    st.markdown(f"- {url}")
        if cs_recommended:
            _render_cs_alert(key=f"new_{len(st.session_state.chat_messages)}")

    st.session_state.chat_messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "cs_recommended": cs_recommended,
        }
    )


def _render_cs_alert(key: str) -> None:
    """day04 승인 기준: 회수·부작용 경보 발견 시 자동 연결 대신 버튼만 노출한다."""
    components.warning_banner("회수·안전성 경보와 관련된 내용이 발견됐어요. CS 상담 연결을 권장해요.")
    if st.button("🙋 CS 상담 연결하기", key=f"cs_alert_{key}"):
        st.toast("(데모) 실제 서비스에서는 CS 상담 페이지로 연결됩니다.")
