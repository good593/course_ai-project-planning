"""상품 조회 API. 다른 기능(추천/성분설명/복용정보)의 기초가 되는 기본 CRUD 성격의 라우터."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductDetail, ProductSummary
from app.services import product_service

router = APIRouter(prefix="/products", tags=["상품"])


@router.get("", response_model=list[ProductSummary])
def read_products(
    카테고리: str | None = None,
    키워드: str | None = None,
    db: Session = Depends(get_db),
):
    """상품 목록 조회. 카테고리/키워드로 필터링할 수 있다."""
    return product_service.list_products(db, 카테고리=카테고리, 키워드=키워드)


@router.get("/{product_id}", response_model=ProductDetail)
def read_product(product_id: str, db: Session = Depends(get_db)):
    """상품 상세 조회.

    주의: 경로 파라미터 이름은 영문(product_id)으로 둔다. Starlette의 경로 파라미터
    정규식(PARAM_REGEX)이 ASCII 식별자만 인식하기 때문에, {상품ID}처럼 한글을 쓰면
    파라미터로 인식되지 않고 리터럴 문자로 취급되어 라우팅이 매칭되지 않는다.
    """
    product = product_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return product
