"""RF-4 복용 정보 안내 API (규칙 기반)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dosage import (
    DosageQuery,
    OverconsumptionCheckRequest,
    OverconsumptionCheckResponse,
    ProductDosageInfo,
)
from app.services import dosage_service

router = APIRouter(prefix="/dosage", tags=["복용 정보 안내"])


@router.get("/products/{product_id}", response_model=ProductDosageInfo)
def read_product_dosage(
    product_id: str,
    연령대: str | None = None,
    성별: str | None = None,
    임신여부: str | None = None,
    수유여부: str | None = None,
    db: Session = Depends(get_db),
):
    """RF-4.1 권장/상한 섭취량 표시: 상품의 주요원료 기준 섭취기준을 보여준다.

    경로 파라미터 이름은 영문(product_id)으로 둔다. Starlette이 경로 파라미터를
    ASCII 식별자로만 인식하므로 {상품ID}처럼 한글을 쓰면 매칭되지 않는다.
    """
    조건 = DosageQuery(연령대=연령대, 성별=성별, 임신여부=임신여부, 수유여부=수유여부)
    result = dosage_service.get_product_dosage(db, product_id, 조건)
    if result is None:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return result


@router.post("/overconsumption-check", response_model=OverconsumptionCheckResponse)
def check_overconsumption(
    request: OverconsumptionCheckRequest, db: Session = Depends(get_db)
):
    """RF-4.2 과다섭취 경고 안내: 여러 상품을 함께 담았을 때 중복 성분을 규칙 기반으로 점검한다.

    RF-4.3(문구를 AI가 보조 생성)은 LLM 기능이므로 이 프로젝트에서는 제외하고,
    고정된 안내 문구를 사용한다.
    """
    return dosage_service.check_overconsumption(
        db, request.상품ID_목록, request.조건
    )
