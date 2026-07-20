"""상품 테이블 ORM 모델 (Day04에서 구축한 건강한하루.db의 '상품' 테이블)."""
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "상품"

    상품ID: Mapped[str] = mapped_column(String, primary_key=True)
    상품명: Mapped[str] = mapped_column(String)
    업소명: Mapped[str] = mapped_column(String)
    카테고리: Mapped[str] = mapped_column(String)
    검색키워드: Mapped[str] = mapped_column("검색키워드(주요원료)", String)
    관련_증상: Mapped[str] = mapped_column(String)
    신고번호: Mapped[str | None] = mapped_column(String, nullable=True)
    등록일자: Mapped[str | None] = mapped_column(String, nullable=True)
    소비기한: Mapped[str | None] = mapped_column(String, nullable=True)
    성상: Mapped[str | None] = mapped_column(String, nullable=True)
    섭취량_섭취방법: Mapped[str | None] = mapped_column(String, nullable=True)
    섭취시주의사항: Mapped[str | None] = mapped_column(String, nullable=True)
    기능성_내용: Mapped[str | None] = mapped_column(String, nullable=True)
    신고번호_상세조회URL: Mapped[str | None] = mapped_column(String, nullable=True)
    데이터출처: Mapped[str | None] = mapped_column(String, nullable=True)
