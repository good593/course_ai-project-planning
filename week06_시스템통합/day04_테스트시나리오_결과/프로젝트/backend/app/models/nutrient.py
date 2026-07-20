"""영양소 관련 테이블 ORM 모델.

- NutrientFunction   : '영양소_기능성' 테이블 (RF-2 성분 설명의 근거 데이터)
- IntakeStandard     : '영양소_섭취기준' 테이블 (RF-4 복용 정보 안내의 기준 데이터)
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NutrientFunction(Base):
    __tablename__ = "영양소_기능성"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    영양소: Mapped[str] = mapped_column(String)
    분류: Mapped[str | None] = mapped_column(String, nullable=True)
    기능성: Mapped[str] = mapped_column(String)
    관련_증상: Mapped[str | None] = mapped_column(String, nullable=True)
    키워드: Mapped[str | None] = mapped_column(String, nullable=True)
    근거_수준: Mapped[str | None] = mapped_column(String, nullable=True)
    근거_설명: Mapped[str | None] = mapped_column(String, nullable=True)
    신뢰도: Mapped[str | None] = mapped_column(String, nullable=True)
    출처: Mapped[str | None] = mapped_column(String, nullable=True)
    출처_URL: Mapped[str | None] = mapped_column(String, nullable=True)


class IntakeStandard(Base):
    __tablename__ = "영양소_섭취기준"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    영양소: Mapped[str] = mapped_column(String)
    연령대: Mapped[str | None] = mapped_column(String, nullable=True)
    성별: Mapped[str | None] = mapped_column(String, nullable=True)
    임신여부: Mapped[str | None] = mapped_column(String, nullable=True)
    수유여부: Mapped[str | None] = mapped_column(String, nullable=True)
    권장섭취량: Mapped[str | None] = mapped_column(String, nullable=True)
    충분섭취량: Mapped[str | None] = mapped_column(String, nullable=True)
    상한섭취량: Mapped[str | None] = mapped_column(String, nullable=True)
    단위: Mapped[str | None] = mapped_column(String, nullable=True)
    출처: Mapped[str | None] = mapped_column(String, nullable=True)
    기관: Mapped[str | None] = mapped_column(String, nullable=True)
    비고: Mapped[str | None] = mapped_column(String, nullable=True)
    출처_URL: Mapped[str | None] = mapped_column(String, nullable=True)
