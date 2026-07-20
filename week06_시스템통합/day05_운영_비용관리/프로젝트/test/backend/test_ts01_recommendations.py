# -*- coding: utf-8 -*-
"""TS-01: 건강고민을 입력해 맞춤 상품을 추천받는다.

관련 API: POST /recommendations
대상 TC: TC-001, TC-002, TC-003 (테스트시나리오_테스트결과.xlsx > 'TC 상세' 시트)

이 파일은 규칙 기반(LLM 미사용) 로직이므로 결과가 항상 같다.
DB(backend/data/건강한하루.db)의 실제 데이터를 기준으로 값을 검증하며,
DB 내용이 바뀌면 이 테스트도 함께 업데이트해야 한다.
"""


def test_tc001_health_concern_recommendation(client):
    """TC-001: '눈 피로' 선택 → 추천 결과가 추천 근거와 함께 표시된다.

    사전 조건: 홈 화면 진입(=API 관점에서는 별도 조건 없음)
    통과 기준: 추천 개수 <= 5, 각 카드에 추천 근거가 표시됨
    """
    response = client.post("/recommendations", json={"건강고민": "눈 피로", "offset": 0})
    assert response.status_code == 200

    data = response.json()
    assert data["건강고민"] == "눈 피로"
    assert data["전체_매칭_건수"] >= 1
    assert len(data["추천상품"]) <= 5

    for item in data["추천상품"]:
        # RF-1.3: 추천근거(관련 증상·주요원료)가 비어 있으면 안 된다.
        assert len(item["추천근거"]) >= 1
        for reason in item["추천근거"]:
            assert reason["영양소"]
            assert reason["기능성"]


def test_tc002_repeat_recommendation_no_overlap(client):
    """TC-002: 재추천(다음 추천) 시 이전과 겹치지 않는 다음 offset 상품이 표시된다.

    '피로' 건강고민은 DB 기준 10건이 매칭되어(page size=5) 정확히 2페이지로
    나뉘므로, 재추천 흐름과 offset 종료 조건을 함께 검증하기 좋다.
    """
    first = client.post("/recommendations", json={"건강고민": "피로", "offset": 0})
    assert first.status_code == 200
    first_data = first.json()

    assert len(first_data["추천상품"]) == 5
    assert first_data["다음_재추천_offset"] == 5

    second = client.post(
        "/recommendations", json={"건강고민": "피로", "offset": first_data["다음_재추천_offset"]}
    )
    assert second.status_code == 200
    second_data = second.json()

    first_ids = {item["상품"]["상품ID"] for item in first_data["추천상품"]}
    second_ids = {item["상품"]["상품ID"] for item in second_data["추천상품"]}

    # 이전 결과와 상품이 중복되지 않아야 한다.
    assert first_ids.isdisjoint(second_ids)
    # 전체 매칭 건수(10건)를 모두 소진했으므로 더 이상 다음 페이지가 없어야 한다.
    assert second_data["다음_재추천_offset"] is None


def test_tc003_no_matching_products_returns_empty_result(client):
    """TC-003: 매칭 상품이 없는 건강고민 조합은 에러 없이 빈 결과로 안내된다.

    통과 기준: 에러 없이 빈 상태 안내(전체_매칭_건수=0, 추천상품=[])가 내려온다.
    (화면이 깨지지 않는지는 frontend에서 이 응답을 받아 안내 문구를 그리는지로 확인한다.)
    """
    response = client.post(
        "/recommendations", json={"건강고민": "존재하지않는고민", "offset": 0}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["전체_매칭_건수"] == 0
    assert data["추천상품"] == []
    assert data["다음_재추천_offset"] is None
