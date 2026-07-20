# -*- coding: utf-8 -*-
"""frontend 테스트 공통 fixture.

`frontend/pyproject.toml` 의 [tool.pytest.ini_options] 에서
`pythonpath = ["streamlit_app"]` 를 설정해 두었으므로, frontend/ 안에서
`uv run pytest` 를 실행하면 streamlit_app/ 안의 모듈(api_client, config 등)을
Streamlit이 실행할 때와 동일하게 flat import(`import api_client`)로 가져올 수 있다.
"""
import pytest


class DummyResponse:
    """requests.Response를 흉내 내는 가짜 응답 객체(실제 네트워크 호출 없이 테스트하기 위함)."""

    def __init__(self, status_code: int, json_data=None, raise_json_error: bool = False):
        self.status_code = status_code
        self._json_data = json_data
        self._raise_json_error = raise_json_error

    def json(self):
        if self._raise_json_error:
            raise ValueError("본문이 JSON이 아닙니다.")
        return self._json_data


@pytest.fixture
def dummy_response():
    return DummyResponse
