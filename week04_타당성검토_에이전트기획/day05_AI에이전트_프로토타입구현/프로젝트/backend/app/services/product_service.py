"""상품 조회 관련 비즈니스 로직."""
from sqlalchemy.orm import Session

from app.models.product import Product


def list_products(
    db: Session, 카테고리: str | None = None, 키워드: str | None = None
) -> list[Product]:
    """카테고리/키워드로 상품 목록을 조회한다. 조건이 없으면 전체를 반환한다."""
    query = db.query(Product)
    if 카테고리:
        query = query.filter(Product.카테고리 == 카테고리)
    if 키워드:
        query = query.filter(
            Product.상품명.like(f"%{키워드}%") | Product.검색키워드.like(f"%{키워드}%")
        )
    return query.order_by(Product.상품ID).all()


def get_product(db: Session, 상품ID: str) -> Product | None:
    """상품ID로 단일 상품 상세 정보를 조회한다."""
    return db.get(Product, 상품ID)
