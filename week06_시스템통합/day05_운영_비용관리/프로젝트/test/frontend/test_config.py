# -*- coding: utf-8 -*-
"""frontend/streamlit_app/config.py 설정값 무결성 테스트.

화면에서 쓰는 선택지 목록이 비어있지 않은지, 홈 화면의 '자주 찾는 고민' 칩이
전체 건강고민 목록의 부분집합인지 등 화면이 깨질 수 있는 설정 오류를
사람이 놓치기 전에 잡아낸다.
"""
import config


def test_health_concerns_not_empty():
    assert len(config.HEALTH_CONCERNS) > 0


def test_home_quick_concerns_is_subset_of_health_concerns():
    """홈 화면 칩(HOME_QUICK_CONCERNS)에만 있고 건강고민입력 화면(HEALTH_CONCERNS)에는
    없는 항목이 있으면, 칩을 눌렀을 때 뒤 화면 상태와 어긋날 수 있다."""
    assert set(config.HOME_QUICK_CONCERNS).issubset(set(config.HEALTH_CONCERNS))


def test_age_groups_and_genders_not_empty():
    assert len(config.AGE_GROUPS) > 0
    assert len(config.GENDERS) > 0


def test_timeouts_are_positive_and_chat_timeout_is_generous():
    assert config.API_TIMEOUT_SECONDS > 0
    assert config.CHAT_TIMEOUT_SECONDS > 0
    # RF-3(AI상담)는 RAG+LLM+외부 Tool 호출이 이어질 수 있어 다른 API보다
    # 오래 걸리므로, 일반 API 타임아웃보다 짧으면 항상 먼저 실패하게 된다.
    assert config.CHAT_TIMEOUT_SECONDS >= config.API_TIMEOUT_SECONDS


def test_recommendation_page_size_matches_backend_default():
    """backend의 RECOMMENDATION_PAGE_SIZE(5)와 어긋나면 재추천 offset 계산이 틀어진다."""
    assert config.RECOMMENDATION_PAGE_SIZE == 5
