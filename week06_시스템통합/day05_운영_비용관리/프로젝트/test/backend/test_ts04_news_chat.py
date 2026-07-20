# -*- coding: utf-8 -*-
"""TS-04: AI상담에서 외부 뉴스를 조회해 답한다.

관련 API: POST /chat (search_supplement_news)
대상 TC: TC-009

실제 GROQ/Tavily 호출이 발생하므로 RUN_LIVE_AI_TESTS=1 로 실행할 때만 동작한다.
(자세한 내용은 test_ts03_rag_chat.py 상단 설명 참고)
"""
import re

from conftest import skip_unless_live_ai

_URL_PATTERN = re.compile(r"^https?://")


@skip_unless_live_ai
def test_tc009_external_news_search(client):
    """TC-009: 최신 뉴스 질문에 search_supplement_news를 호출해 출처 URL과 함께 답한다."""
    response = client.post(
        "/chat", json={"message": "루테인 관련 최신 뉴스 있어?", "history": []}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["answer"]
    assert len(data["출처_URL_목록"]) >= 1, "외부 뉴스 검색 결과의 출처 URL이 노출되어야 한다."
    for url in data["출처_URL_목록"]:
        assert _URL_PATTERN.match(url), f"출처 URL 형식이 올바르지 않습니다: {url}"

    print(f"\n[TC-009 answer]\n{data['answer']}")
    print(f"[TC-009 출처_URL_목록] {data['출처_URL_목록']}")
    print(
        "[TC-009 참고] 출처 URL이 실제로 접속 가능한지는 이 테스트에서 네트워크로 "
        "재확인하지 않습니다(사내망 등에서 불안정할 수 있어 의도적으로 제외). "
        "학생이 직접 링크를 열어 확인해주세요."
    )
