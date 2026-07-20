"""프론트엔드 환경설정.

Week03 화면설계서(day03)와 사용자 시나리오(day04)에서 정한 값을
학생들이 한눈에 볼 수 있도록 이 파일 하나에 모아둔다.
"""
import os

# backend/ FastAPI 서버 주소. 다른 포트로 띄웠다면 환경변수로 덮어쓸 수 있다.
#   Windows PowerShell: $env:HEALTHY_DAY_API_BASE_URL = "http://localhost:8001"
API_BASE_URL = os.environ.get("HEALTHY_DAY_API_BASE_URL", "http://localhost:8001")

# NFR-1.0 참고: 추천 2초, RAG 5초 이내 응답이 기준이므로, 그보다 넉넉하게 타임아웃을 둔다.
API_TIMEOUT_SECONDS = 8

APP_TITLE = "건강한하루"
APP_ICON = "🥗"

# RF-1.2: 추천 상품은 최대 5개까지 노출한다(backend RECOMMENDATION_PAGE_SIZE와 동일).
RECOMMENDATION_PAGE_SIZE = 5

# 건강고민입력(UI-W-002) 멀티셀렉트 옵션.
# data/건강한하루.db의 상품.관련_증상 컬럼에 실제로 존재하는 값과 동일하게 맞춰야
# RF-1 추천 매칭(LIKE 검색)이 정상적으로 동작한다.
HEALTH_CONCERNS = [
    "피로", "눈 피로", "수면", "면역력 저하", "관절 통증", "스트레스",
    "혈액순환", "다이어트", "기억력 저하", "골 건강", "변비", "간 피로",
    "노화", "빈혈", "골다공증", "배뇨",
]

# 홈(UI-W-001) 카테고리 칩에는 자주 찾는 고민만 추려서 보여준다.
HOME_QUICK_CONCERNS = ["눈 피로", "피로", "면역력 저하", "관절 통증", "수면", "스트레스"]

# 상품상세(UI-H-004) 섭취기준 조회에 사용하는 선택지 (backend 영양소_섭취기준 테이블 기준).
AGE_GROUPS = ["19~29세", "30~49세", "50~64세", "65세 이상", "임산부", "수유부"]
GENDERS = ["여성", "남성"]
