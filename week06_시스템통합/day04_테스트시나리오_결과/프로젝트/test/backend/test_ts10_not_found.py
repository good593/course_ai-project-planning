# -*- coding: utf-8 -*-
"""TS-10: 잘못된 입력·존재하지 않는 데이터를 조회했을 때 오류를 안내한다.

관련 API: GET /dosage/products/{product_id}, GET /nutrients/{nutrient_name}
대상 TC: TC-021, TC-022
"""


def test_tc021_unknown_product_id_returns_404(client):
    """TC-021: 존재하지 않는 상품ID 조회 시 404와 안내 메시지를 반환한다."""
    response = client.get("/dosage/products/존재하지않는ID")
    assert response.status_code == 404
    assert response.json()["detail"] == "상품을 찾을 수 없습니다."


def test_tc022_unknown_nutrient_name_returns_404(client):
    """TC-022: 존재하지 않는 성분명 조회 시 404와 안내 메시지를 반환한다."""
    response = client.get("/nutrients/존재하지않는성분XYZ")
    assert response.status_code == 404
    assert response.json()["detail"] == "해당 영양소 정보를 찾을 수 없습니다."
