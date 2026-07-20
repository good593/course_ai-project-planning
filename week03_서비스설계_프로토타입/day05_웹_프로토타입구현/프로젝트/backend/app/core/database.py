"""DB 연결/세션 관리.

SQLAlchemy의 엔진과 세션을 한 곳에서 만들어, 다른 모듈은 이 파일에서
`get_db` 의존성만 가져다 쓰면 되도록 구성한다.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

# 기존 테이블(상품/영양소_기능성/영양소_섭취기준)은 한글 컬럼명을 그대로 사용하므로
# check_same_thread=False 만 추가해 FastAPI의 여러 요청에서 커넥션을 재사용할 수 있게 한다.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """모든 ORM 모델이 상속받는 기본 클래스."""


def get_db():
    """요청마다 새 세션을 열고, 끝나면 반드시 닫아주는 FastAPI 의존성."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
