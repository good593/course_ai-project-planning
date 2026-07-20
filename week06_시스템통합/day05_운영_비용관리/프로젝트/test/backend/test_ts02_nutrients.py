# -*- coding: utf-8 -*-
"""TS-02: 상품상세에서 성분을 쉬운 설명으로 확인한다.

관련 API: GET /nutrients/{nutrient_name}
대상 TC: TC-004, TC-005
"""


def test_tc004_nutrient_explanation_with_source(client):
    """TC-004: '루테인' 성분명 조회 시 쉬운 설명과 근거 출처가 함께 표시된다."""
    response = client.get("/nutrients/루테인")
    assert response.status_code == 200

    data = response.json()
    assert data["영양소"] == "루테인"
    assert len(data["기능성_목록"]) >= 1

    for item in data["기능성_목록"]:
        assert item["기능성"]  # 쉬운 설명(기능성 문구)이 비어 있으면 안 됨
        assert item["출처"]  # 근거 출처(기관·문헌)가 함께 노출되어야 함


def test_tc005_unknown_nutrient_returns_404(client):
    """TC-005: DB에 없는 성분명을 조회하면 404와 안내 메시지를 반환한다."""
    response = client.get("/nutrients/존재하지않는성분")
    assert response.status_code == 404
    assert response.json()["detail"] == "해당 영양소 정보를 찾을 수 없습니다."
