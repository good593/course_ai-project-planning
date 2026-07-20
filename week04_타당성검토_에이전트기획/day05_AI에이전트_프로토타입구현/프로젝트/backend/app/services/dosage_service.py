"""RF-4 복용 정보 안내 로직.

RF-4.1 권장/상한 섭취량 표시와 RF-4.2 과다섭취 경고 안내는
요구사항정의서 변경내역에 따라 AI가 아닌 규칙 기반으로 판단한다.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.nutrient import IntakeStandard
from app.models.product import Product
from app.schemas.dosage import (
    DosageQuery,
    OverconsumptionCheckResponse,
    OverconsumptionWarning,
    ProductDosageInfo,
)
from app.schemas.nutrient import IntakeStandardOut


def get_intake_standards(
    db: Session, 영양소: str, 조건: DosageQuery
) -> list[IntakeStandard]:
    """사용자 조건(연령대/성별/임신·수유 여부)에 맞는 섭취기준 행을 찾는다."""
    query = db.query(IntakeStandard).filter(IntakeStandard.영양소 == 영양소)
    if 조건.연령대:
        query = query.filter(IntakeStandard.연령대 == 조건.연령대)
    if 조건.성별:
        query = query.filter(IntakeStandard.성별 == 조건.성별)
    if 조건.임신여부:
        query = query.filter(IntakeStandard.임신여부 == 조건.임신여부)
    if 조건.수유여부:
        query = query.filter(IntakeStandard.수유여부 == 조건.수유여부)
    return query.all()


def get_product_dosage(
    db: Session, 상품ID: str, 조건: DosageQuery
) -> ProductDosageInfo | None:
    """RF-4.1: 상품 하나의 주요원료 기준 권장/상한 섭취량을 조회한다."""
    product = db.get(Product, 상품ID)
    if product is None:
        return None
    standards = get_intake_standards(db, product.검색키워드, 조건)
    return ProductDosageInfo(
        상품ID=product.상품ID,
        상품명=product.상품명,
        주요원료=product.검색키워드,
        섭취기준=[IntakeStandardOut.model_validate(s) for s in standards],
    )


def check_overconsumption(
    db: Session, 상품ID_목록: list[str], 조건: DosageQuery
) -> OverconsumptionCheckResponse:
    """RF-4.2 과다섭취 경고 안내 (규칙 기반).

    함량(mg) 데이터가 없어 정확한 합산 섭취량 계산은 불가능하므로,
    장바구니에 동일 원료가 2개 이상 상품에 중복 포함되면 경고하는
    간이 규칙을 사용한다. RF-4.3처럼 문구 생성에 AI를 쓰지 않고 고정 문구를 사용한다.
    """
    products = db.query(Product).filter(Product.상품ID.in_(상품ID_목록)).all()

    products_by_nutrient: dict[str, list[str]] = defaultdict(list)
    for product in products:
        products_by_nutrient[product.검색키워드].append(product.상품명)

    경고_목록: list[OverconsumptionWarning] = []
    for 영양소, 상품명_목록 in products_by_nutrient.items():
        if len(상품명_목록) < 2:
            continue
        standards = get_intake_standards(db, 영양소, 조건)
        상한섭취량 = standards[0].상한섭취량 if standards else None
        단위 = standards[0].단위 if standards else None
        기준_표시 = f"{상한섭취량}{단위}" if 상한섭취량 else "기준 미확인"
        경고_목록.append(
            OverconsumptionWarning(
                영양소=영양소,
                중복_상품수=len(상품명_목록),
                중복_상품명=상품명_목록,
                상한섭취량=상한섭취량,
                단위=단위,
                경고_문구=(
                    f"'{영양소}' 성분이 {len(상품명_목록)}개 상품에 중복 포함되어 있습니다. "
                    f"합산 섭취량이 상한섭취량({기준_표시})을 넘지 않는지 확인하세요."
                ),
            )
        )

    안내 = (
        "실제 함량(mg) 데이터가 없어 상품 중복 여부로만 판단하는 간이 규칙입니다. "
        "정확한 판단은 제품 라벨의 실제 함량을 확인하세요."
        if 경고_목록
        else "중복 섭취 위험이 있는 성분이 발견되지 않았습니다."
    )

    return OverconsumptionCheckResponse(
        확인_상품수=len(products), 경고_목록=경고_목록, 안내=안내
    )
