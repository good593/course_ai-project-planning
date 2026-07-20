# -*- coding: utf-8 -*-
"""frontend/streamlit_app/api_client.py 단위 테스트.

화면(ui/*.py)은 항상 api_client의 함수만 호출하고, requests의 세부사항은
api_client 안에서만 다룬다. 여기서는 실제 backend 서버를 띄우지 않고
requests.request를 흉내 내어(mock) 다음을 검증한다.

  - day04 사용자 시나리오 문서의 '예외 흐름 5(연결 실패/응답 지연)'가
    ApiConnectionError로 올바르게 변환되는가
  - backend가 404/그 외 4xx·5xx를 반환했을 때 ApiNotFoundError/ApiError로
    올바르게 변환되고, backend가 준 안내 메시지(detail)를 그대로 살리는가
    (테스트시나리오_테스트결과.xlsx의 TC-005/TC-016/TC-021/TC-022가
    화면에 실제로 어떻게 도달하는지의 frontend 쪽 대응 테스트)
  - 사이드바 헬스체크(health_check)가 연결 성공/실패를 올바르게 판정하는가
"""
from unittest.mock import patch

import pytest
import requests

import api_client
import config


def test_recommend_success_returns_parsed_json(dummy_response):
    """정상 응답이면 requests 응답의 JSON을 그대로 반환한다."""
    fake_json = {"건강고민": "눈 피로", "전체_매칭_건수": 2, "추천상품": [], "다음_재추천_offset": None}
    with patch("api_client.requests.request", return_value=dummy_response(200, fake_json)) as mock_request:
        result = api_client.recommend("눈 피로", offset=0)

    assert result == fake_json
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert args[1] == f"{config.API_BASE_URL}/recommendations"
    assert kwargs["json"] == {"건강고민": "눈 피로", "offset": 0}


def test_connection_error_is_wrapped_as_api_connection_error():
    """backend 서버(FastAPI)가 꺼져 있으면 ApiConnectionError로 변환되어야 한다."""
    with patch("api_client.requests.request", side_effect=requests.exceptions.ConnectionError()):
        with pytest.raises(api_client.ApiConnectionError) as exc_info:
            api_client.get_product("P001")

    assert "백엔드 서버" in exc_info.value.message


def test_timeout_is_wrapped_as_api_connection_error():
    """응답이 지연되면(Timeout) 사용자에게 재시도를 안내하는 ApiConnectionError로 변환된다."""
    with patch("api_client.requests.request", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(api_client.ApiConnectionError) as exc_info:
            api_client.get_nutrient_explanation("루테인")

    assert "지연" in exc_info.value.message


def test_404_is_wrapped_as_api_not_found_error_with_backend_detail(dummy_response):
    """backend가 404 + detail을 반환하면, detail 메시지를 그대로 살려 ApiNotFoundError를 던진다."""
    body = {"detail": "해당 영양소 정보를 찾을 수 없습니다."}
    with patch("api_client.requests.request", return_value=dummy_response(404, body)):
        with pytest.raises(api_client.ApiNotFoundError) as exc_info:
            api_client.get_nutrient_explanation("존재하지않는성분")

    assert exc_info.value.message == "해당 영양소 정보를 찾을 수 없습니다."


def test_404_without_json_body_uses_default_message(dummy_response):
    """backend 응답 본문이 JSON이 아니어도(예상 밖 상황) 기본 안내 메시지로 대체한다."""
    with patch(
        "api_client.requests.request",
        return_value=dummy_response(404, raise_json_error=True),
    ):
        with pytest.raises(api_client.ApiNotFoundError) as exc_info:
            api_client.get_product("존재하지않는ID")

    assert exc_info.value.message == "요청한 정보를 찾을 수 없습니다."


def test_5xx_is_wrapped_as_api_error(dummy_response):
    """503(예: GROQ/TAVILY 키 미설정) 등 그 외 오류도 detail 메시지와 함께 ApiError로 변환된다."""
    body = {"detail": "AI 상담 기능을 사용하려면 backend/.env 에 GROQ_API_KEY 값을 설정해야 합니다."}
    with patch("api_client.requests.request", return_value=dummy_response(503, body)):
        with pytest.raises(api_client.ApiError) as exc_info:
            api_client.chat("루테인이 뭐야?", history=[])

    assert "GROQ_API_KEY" in exc_info.value.message
    assert not isinstance(exc_info.value, api_client.ApiNotFoundError)


def test_health_check_true_when_backend_reachable(dummy_response):
    with patch("api_client.requests.request", return_value=dummy_response(200, {"status": "ok"})):
        assert api_client.health_check() is True


def test_health_check_false_when_backend_unreachable():
    with patch("api_client.requests.request", side_effect=requests.exceptions.ConnectionError()):
        assert api_client.health_check() is False


def test_check_overconsumption_sends_expected_payload(dummy_response):
    """중복 성분 확인 요청(RF-4.2) 시 상품ID 목록과 조건이 그대로 backend에 전달되는지 확인한다."""
    fake_json = {"확인_상품수": 2, "경고_목록": [], "안내": "중복 섭취 위험이 있는 성분이 발견되지 않았습니다."}
    with patch("api_client.requests.request", return_value=dummy_response(200, fake_json)) as mock_request:
        result = api_client.check_overconsumption(["P001", "P002"], {"연령대": "19~29세"})

    assert result == fake_json
    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {
        "상품ID_목록": ["P001", "P002"],
        "조건": {"연령대": "19~29세"},
    }


def test_chat_uses_dedicated_longer_timeout(dummy_response):
    """RF-3 AI상담은 다른 API보다 오래 걸릴 수 있으므로 별도의 긴 타임아웃을 사용해야 한다."""
    with patch("api_client.requests.request", return_value=dummy_response(200, {"answer": "ok"})) as mock_request:
        api_client.chat("안녕", history=[])

    _, kwargs = mock_request.call_args
    assert kwargs["timeout"] == config.CHAT_TIMEOUT_SECONDS
    assert config.CHAT_TIMEOUT_SECONDS >= config.API_TIMEOUT_SECONDS
