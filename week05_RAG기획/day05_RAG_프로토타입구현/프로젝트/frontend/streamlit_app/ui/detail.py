"""상품 상세 (UI-H-004) — day03 와이어프레임_디스크립션/UI-H-004 참고."""
import streamlit as st

import api_client
from config import AGE_GROUPS, GENDERS
from state import go
from ui import components


def render() -> None:
    product_id = st.session_state.selected_product_id
    if not product_id:
        go("result")
        return

    try:
        product = api_client.get_product(product_id)
    except api_client.ApiError as exc:
        components.api_error_banner(exc)
        if st.button("추천결과로 돌아가기"):
            go("result")
        return

    col_image, col_info = st.columns([1, 3])
    with col_image:
        st.markdown(
            "<div style='font-size:64px;text-align:center'>🧴</div>",
            unsafe_allow_html=True,
        )
    with col_info:
        st.subheader(product["상품명"])
        st.caption(f"{product['업소명']} · 신고번호 {product.get('신고번호') or '-'}")
        st.markdown(f"`{product['관련_증상']}` 관련 기능성")

    st.divider()

    st.markdown("#### 성분 쉬운 설명")
    _render_nutrient_explanation(product["검색키워드"])

    st.markdown("#### 섭취방법 · 주의사항")
    st.write(product.get("섭취량_섭취방법") or "등록된 섭취방법 정보가 없습니다.")
    if product.get("섭취시주의사항"):
        components.warning_banner(product["섭취시주의사항"])

    st.markdown("#### 권장 · 상한 섭취량")
    _render_dosage(product_id)

    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("← 추천결과로"):
            go("result")
    with btn_col2:
        if st.button("구매하기", type="primary", use_container_width=True):
            st.success("(데모) 실제 서비스에서는 판매 채널 또는 장바구니로 연결됩니다.")


def _render_nutrient_explanation(nutrient_name: str) -> None:
    """RF-2 성분 쉬운 설명 (Should). 정보가 없어도 상세 페이지 흐름은 끊기지 않는다."""
    try:
        explanation = api_client.get_nutrient_explanation(nutrient_name)
    except api_client.ApiNotFoundError:
        st.info("이 성분에 대한 쉬운 설명을 아직 준비하지 못했어요.")
        return
    except api_client.ApiError as exc:
        components.api_error_banner(exc)
        return

    for item in explanation["기능성_목록"][:3]:
        st.write(f"- {item['기능성']}")
        if item.get("출처"):
            st.caption(f"출처: {item['출처']}")


def _render_dosage(product_id: str) -> None:
    """RF-4.1 권장/상한 섭취량 표시. 연령대·성별에 따라 값이 달라진다."""
    c1, c2 = st.columns(2)
    age_group = c1.selectbox("연령대", AGE_GROUPS, index=AGE_GROUPS.index(st.session_state.age_group))
    gender = c2.selectbox("성별", GENDERS, index=GENDERS.index(st.session_state.gender))
    st.session_state.age_group = age_group
    st.session_state.gender = gender

    try:
        dosage = api_client.get_product_dosage(product_id, 연령대=age_group, 성별=gender)
    except api_client.ApiNotFoundError:
        st.info("이 상품과 매칭되는 섭취기준을 찾지 못했어요.")
        return
    except api_client.ApiError as exc:
        components.api_error_banner(exc)
        return

    for standard in dosage["섭취기준"]:
        badge_col1, badge_col2 = st.columns(2)
        badge_col1.metric("권장섭취량", f"{standard['권장섭취량'] or '-'} {standard['단위'] or ''}")
        badge_col2.metric("상한섭취량", f"{standard['상한섭취량'] or '-'} {standard['단위'] or ''}")

    st.caption(
        "다른 제품과 함께 섭취할 계획이라면 추천결과 화면의 "
        "'여러 상품을 함께 섭취해도 될까요?' 기능으로 확인해보세요."
    )
