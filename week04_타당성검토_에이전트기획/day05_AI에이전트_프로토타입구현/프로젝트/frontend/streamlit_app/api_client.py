"""backend/ FastAPI 서버를 호출하는 얇은 클라이언트.

화면(ui/*.py)은 이 모듈의 함수만 호출하고, requests의 세부사항(타임아웃,
상태코드 처리 등)은 이 파일 안에서만 다룬다. day04 사용자 시나리오 문서의
"예외 흐름 5. 응답 지연"과 연결 실패 상황을 여기서 공통으로 변환해 준다.
"""
import requests

from config import API_BASE_URL, API_TIMEOUT_SECONDS


class ApiError(Exception):
    """API 호출 중 발생한 문제를 화면에 보여줄 문구와 함께 감싼다."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ApiConnectionError(ApiError):
    """서버 연결 실패 / 응답 지연 (day04 예외 흐름 5)."""


class ApiNotFoundError(ApiError):
    """404: 상품·영양소 등 리소스를 찾을 수 없음."""


def _request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=API_TIMEOUT_SECONDS, **kwargs)
    except requests.exceptions.ConnectionError as exc:
        raise ApiConnectionError(
            "백엔드 서버(FastAPI)에 연결할 수 없어요. backend/ 서버가 실행 중인지 확인해 주세요."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise ApiConnectionError(
            "요청이 지연되고 있어요. 잠시 후 다시 시도해 주세요."
        ) from exc

    if response.status_code == 404:
        detail = _safe_detail(response, default="요청한 정보를 찾을 수 없습니다.")
        raise ApiNotFoundError(detail)
    if response.status_code >= 400:
        detail = _safe_detail(response, default="요청을 처리하지 못했습니다.")
        raise ApiError(detail)

    return response.json()


def _safe_detail(response: requests.Response, default: str) -> str:
    try:
        return response.json().get("detail", default)
    except ValueError:
        return default


# ── RF-1: AI 맞춤 상품 추천 ─────────────────────────
def recommend(건강고민: str, offset: int = 0) -> dict:
    return _request(
        "POST", "/recommendations", json={"건강고민": 건강고민, "offset": offset}
    )


# ── 상품 조회 ───────────────────────────────────────
def list_products(카테고리: str | None = None, 키워드: str | None = None) -> list[dict]:
    params = {k: v for k, v in {"카테고리": 카테고리, "키워드": 키워드}.items() if v}
    return _request("GET", "/products", params=params)


def get_product(product_id: str) -> dict:
    return _request("GET", f"/products/{product_id}")


# ── RF-2: AI 성분 설명 ─────────────────────────────
def get_nutrient_explanation(nutrient_name: str) -> dict:
    return _request("GET", f"/nutrients/{nutrient_name}")


# ── RF-4: 복용 정보 안내 ────────────────────────────
def get_product_dosage(
    product_id: str,
    연령대: str | None = None,
    성별: str | None = None,
    임신여부: str | None = None,
    수유여부: str | None = None,
) -> dict:
    params = {
        k: v
        for k, v in {
            "연령대": 연령대,
            "성별": 성별,
            "임신여부": 임신여부,
            "수유여부": 수유여부,
        }.items()
        if v
    }
    return _request("GET", f"/dosage/products/{product_id}", params=params)


def check_overconsumption(상품ID_목록: list[str], 조건: dict) -> dict:
    return _request(
        "POST",
        "/dosage/overconsumption-check",
        json={"상품ID_목록": 상품ID_목록, "조건": 조건},
    )


# ── RF-3: AI 상담 (Agent, 외부 인터넷 조회 도구 포함) ──
def chat(message: str, history: list[dict]) -> dict:
    return _request("POST", "/chat", json={"message": message, "history": history})


def health_check() -> bool:
    """사이드바에 백엔드 연결 상태를 표시하기 위한 가벼운 헬스체크."""
    try:
        _request("GET", "/")
        return True
    except ApiError:
        return False
