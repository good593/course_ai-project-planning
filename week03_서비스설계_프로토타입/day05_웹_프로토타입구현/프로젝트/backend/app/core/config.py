"""애플리케이션 환경설정.

학생들이 한 눈에 볼 수 있도록 설정값을 이 파일 하나에 모아둔다.
"""
from pathlib import Path

# 프로젝트 루트 (이 파일 기준 두 단계 위 = day05_5일차/프로젝트)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Day04에서 구축한 SQLite DB를 그대로 재사용한다.
DB_PATH = BASE_DIR / "data" / "건강한하루.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# RF-1.2 맞춤 추천 결과 제공: 추천 상품은 최대 5개까지 노출한다.
RECOMMENDATION_PAGE_SIZE = 5

APP_TITLE = "건강한하루 API"
APP_DESCRIPTION = "건강기능식품 맞춤 추천 · 성분 설명 · 복용 정보 안내 서비스 (규칙 기반)"
APP_VERSION = "0.1.0"
