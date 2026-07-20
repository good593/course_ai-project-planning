# -*- coding: utf-8 -*-
"""TS-09: 여러 상품을 함께 담았을 때 과다섭취를 경고한다.

관련 API: GET /dosage/products/{product_id}, POST /dosage/overconsumption-check
대상 TC: TC-019, TC-020

사용 데이터(backend/data/건강한하루.db 기준):
- P001(뉴메릿 비타민C&D 메가), P002(뉴메릿 비타민C&D 듀얼 메가) → 둘 다 주요원료 '비타민 C' (중복)
- P004(이지맘 비타민D) → 주요원료 '비타민 D'
"""


def test_tc019_duplicate_nutrient_overconsumption_warning(client):
    """TC-019: 동일 성분(비타민 C)을 포함한 상품 2개를 함께 담으면 중복 경고가 표시된다."""
    response = client.post(
        "/dosage/overconsumption-check",
        json={"상품ID_목록": ["P001", "P002"], "조건": {}},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["확인_상품수"] == 2
    assert len(data["경고_목록"]) >= 1

    warning = next(w for w in data["경고_목록"] if w["영양소"] == "비타민 C")
    assert warning["중복_상품수"] == 2
    assert set(warning["중복_상품명"]) == {
        "뉴메릿 비타민C&D 메가",
        "뉴메릿 비타민C&D 듀얼 메가",
    }
    assert warning["상한섭취량"] == "2000"
    assert warning["단위"] == "mg"
    assert "비타민 C" in warning["경고_문구"]


def test_tc019_no_false_positive_for_single_product(client):
    """TC-019 보조 검증: 중복 성분이 없는 단일 상품은 경고가 발생하지 않아야 한다."""
    response = client.post(
        "/dosage/overconsumption-check",
        json={"상품ID_목록": ["P007"], "조건": {}},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["확인_상품수"] == 1
    assert data["경고_목록"] == []


def test_tc020_dosage_changes_by_condition(client):
    """TC-020: 연령대/성별 조건을 바꾸면 복용 정보(권장/상한 섭취량)가 조건에 맞게 달라진다."""
    default_age = client.get(
        "/dosage/products/P004", params={"연령대": "19~29세", "성별": "여성"}
    )
    assert default_age.status_code == 200
    default_data = default_age.json()
    assert default_data["상품ID"] == "P004"
    assert default_data["주요원료"] == "비타민 D"
    assert len(default_data["섭취기준"]) == 1
    assert default_data["섭취기준"][0]["연령대"] == "19~29세"
    assert default_data["섭취기준"][0]["임신여부"] == "해당없음"

    pregnant = client.get("/dosage/products/P004", params={"연령대": "임산부"})
    assert pregnant.status_code == 200
    pregnant_data = pregnant.json()
    assert len(pregnant_data["섭취기준"]) == 1
    assert pregnant_data["섭취기준"][0]["임신여부"] == "예"

    # 상한섭취량 자체는 DB 기준으로 동일(100μg)하지만, 조건별로 다른 행이 조회되어야 한다.
    assert default_data["섭취기준"][0]["상한섭취량"] == "100"
    assert pregnant_data["섭취기준"][0]["상한섭취량"] == "100"
    assert default_data["섭취기준"][0] != pregnant_data["섭취기준"][0]
