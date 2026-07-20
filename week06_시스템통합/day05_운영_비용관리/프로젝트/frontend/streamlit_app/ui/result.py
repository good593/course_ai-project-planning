"""맞춤 추천 결과 (UI-W-003) — day03 와이어프레임_디스크립션/UI-W-003 참고."""
import streamlit as st

import api_client
from config import AGE_GROUPS, GENDERS
from state import go
from ui import components


def render() -> None:
    concerns = st.session_state.selected_concerns
    if not concerns:
        # 직접 URL 이동 등으로 조건 없이 들어온 경우를 방어적으로 처리한다.
        go("input")
        return

    primary_concern = concerns[0]

    st.caption("선택한 건강고민")
    tag_cols = st.columns([1] * len(concerns) + [3])
    for col, concern in zip(tag_cols, concerns):
        col.markdown(f"`{concern}`")
    with tag_cols[-1]:
        if st.button("고민 다시 입력 ✎", key="edit_concerns"):
            go("input")

    st.divider()

    try:
        with st.spinner("맞춤 상품을 찾고 있어요..."):
            data = api_client.recommend(primary_concern, offset=st.session_state.offset)
    except api_client.ApiError as exc:
        components.api_error_banner(exc)
        return

    # day04 예외 흐름 2. 추천 결과 없음
    if data["전체_매칭_건수"] == 0:
        components.empty_state(
            "조건에 맞는 추천 결과가 없어요.",
            "건강고민 다시 입력하기",
            "input",
        )
        return

    items = data["추천상품"]
    if not items:
        # 재추천을 반복해 더 보여줄 상품이 없는 경우
        st.info("더 이상 추천할 상품이 없어요. 처음부터 다시 볼까요?")
        if st.button("처음부터 다시 보기", type="primary"):
            st.session_state.offset = 0
            st.rerun()
        return

    st.subheader(f"'{primary_concern}'에 도움이 될 수 있는 상품")
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        product = item["상품"]
        reasons = item["추천근거"]
        with col.container(border=True):
            st.markdown("🧴")
            st.markdown(f"**{product['상품명']}**")
            st.caption(f"{product['카테고리']} · {product['관련_증상']}")
            if reasons:
                st.caption(f"근거: {reasons[0]['기능성'][:24]}...")
            if st.button("상세보기", key=f"detail_{product['상품ID']}", use_container_width=True):
                go("detail", selected_product_id=product["상품ID"])

    st.divider()
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if data.get("다음_재추천_offset") is not None:
            if st.button("🔄 재추천 받기"):
                st.session_state.offset = data["다음_재추천_offset"]
                st.rerun()
        else:
            st.caption("더 이상 추천할 상품이 없어요.")
    with action_col2:
        st.caption(f"전체 {data['전체_매칭_건수']}건 중 {len(items)}건 표시 중")

    _render_overconsumption_check(items)


def _render_overconsumption_check(items: list[dict]) -> None:
    """확장 기능(RF-4.2): 여러 상품을 함께 담았을 때 과다섭취 여부를 확인한다.

    Day01 MVP에서는 Won't have로 미룬 기능이지만, backend에 이미 구현되어 있어
    학생들이 전체 API를 한 번씩 호출해볼 수 있도록 선택 기능으로 남겨둔다.
    """
    with st.expander("여러 상품을 함께 섭취해도 될까요? (선택 기능)"):
        options = {
            f"{it['상품']['상품명']} ({it['상품']['상품ID']})": it["상품"]["상품ID"]
            for it in items
        }
        picked_labels = st.multiselect("함께 담을 상품을 2개 이상 선택하세요", options=list(options.keys()))

        c1, c2 = st.columns(2)
        age_group = c1.selectbox("연령대", AGE_GROUPS, index=AGE_GROUPS.index(st.session_state.age_group))
        gender = c2.selectbox("성별", GENDERS, index=GENDERS.index(st.session_state.gender))
        st.session_state.age_group = age_group
        st.session_state.gender = gender

        if st.button("과다섭취 여부 확인", disabled=len(picked_labels) < 2):
            product_ids = [options[label] for label in picked_labels]
            try:
                result = api_client.check_overconsumption(
                    product_ids, {"연령대": age_group, "성별": gender}
                )
            except api_client.ApiError as exc:
                components.api_error_banner(exc)
            else:
                if result["경고_목록"]:
                    # day04 예외 흐름 3. 상한섭취량 초과 경고
                    for warning in result["경고_목록"]:
                        components.warning_banner(warning["경고_문구"])
                else:
                    st.success(result["안내"])
