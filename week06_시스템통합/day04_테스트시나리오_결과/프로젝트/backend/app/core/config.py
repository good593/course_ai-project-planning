"""애플리케이션 환경설정.

학생들이 한 눈에 볼 수 있도록 설정값을 이 파일 하나에 모아둔다.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 (이 파일 기준 두 단계 위 = day05_5일차/프로젝트)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

# Day04에서 구축한 SQLite DB를 그대로 재사용한다.
DB_PATH = BASE_DIR / "data" / "건강한하루.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# RF-1.2 맞춤 추천 결과 제공: 추천 상품은 최대 5개까지 노출한다.
RECOMMENDATION_PAGE_SIZE = 5

APP_TITLE = "건강한하루 API"
APP_DESCRIPTION = "건강기능식품 맞춤 추천 · 성분 설명 · 복용 정보 안내 서비스 (규칙 기반 + RF-3 AI상담 RAG Agent)"
APP_VERSION = "0.3.0"

# ── RF-3 AI상담(Agent) ──────────────────────────────
# week04 day04 "AI 에이전트 챗봇 설계(외부 인터넷 조회 도구)" 문서를 그대로 구현한다.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

# ── RF-3 내부 지식베이스 RAG (week05 day03 노트북을 백엔드 서비스로 옮김) ──
# 임베딩은 로컬 Ollama 모델을 사용하므로 별도 API 키가 필요 없다.
# 사전에 `ollama pull qwen3-embedding:0.6b` 로 모델을 받아두고 `ollama serve`를 띄워야 한다.
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
RAG_COLLECTION_NAME = "healthy-daily-rag"
RAG_TOP_K = 3

# 회수·안전성 경보를 검색할 때 우선 신뢰하는 공공기관 도메인.
RECALL_ALERT_DOMAINS = [
    "www.foodsafetykorea.go.kr",
    "www.mfds.go.kr",
    "www.consumer.go.kr",
]
# 성분·제품 관련 뉴스를 검색할 때 우선 신뢰하는 매체 도메인.
SUPPLEMENT_NEWS_DOMAINS = [
    "news.naver.com",
    "www.foodsafetykorea.go.kr",
    "www.mfds.go.kr",
]
