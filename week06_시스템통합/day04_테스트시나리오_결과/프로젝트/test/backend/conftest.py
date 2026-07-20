# -*- coding: utf-8 -*-
"""backend 테스트 공통 fixture.

`backend/pyproject.toml` 의 [tool.pytest.ini_options] 에서
`pythonpath = ["."]` 를 설정해 두었으므로, backend/ 안에서
`uv run pytest` 를 실행하면 이 파일에서 바로 `app.main` 을 import 할 수 있다.
(프로젝트 루트가 아니라 backend/ 디렉터리 안에서 실행해야 한다.)
"""
import os
import re

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import EMBEDDING_MODEL
from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient. 실제 uvicorn 서버를 띄우지 않고 앱을 직접 호출한다.

    `with` 블록으로 감싸면 startup 이벤트(RAG/Agent 워밍업)도 함께 실행된다.
    워밍업은 실패해도 무시하도록 main.py에 이미 구현되어 있어 안전하다.
    """
    with TestClient(app) as c:
        yield c


# ── RF-3 AI상담(Agent) 라이브 테스트 스킵 조건 ─────────────────────────
# TS-03~TS-07(TC-006~TC-015)은 실제 GROQ/Tavily API를 호출하고 비용·시간이
# 발생하므로, 아래 두 조건을 모두 만족할 때만 실행한다.
#   1) backend/.env 에 GROQ_API_KEY / TAVILY_API_KEY 가 설정되어 있을 것
#   2) 환경변수 RUN_LIVE_AI_TESTS=1 로 실행자가 명시적으로 동의했을 것
# (RAG를 쓰는 케이스는 로컬 Ollama 서버 + 임베딩 모델 준비 여부도 추가로 확인한다.)
RUN_LIVE_AI_TESTS = os.environ.get("RUN_LIVE_AI_TESTS") == "1"


def _live_agent_configured() -> bool:
    from app.core.config import GROQ_API_KEY, TAVILY_API_KEY

    return bool(GROQ_API_KEY and TAVILY_API_KEY)


def _ollama_ready() -> bool:
    """로컬 Ollama 서버가 떠 있고, RAG 임베딩 모델이 pull 되어 있는지 확인한다."""
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=2)
        resp.raise_for_status()
    except Exception:
        return False
    names = [m.get("name", "") for m in resp.json().get("models", [])]
    return any(EMBEDDING_MODEL in name for name in names)


skip_unless_live_ai = pytest.mark.skipif(
    not (RUN_LIVE_AI_TESTS and _live_agent_configured()),
    reason=(
        "실제 LLM 호출 테스트입니다. backend/.env 에 GROQ_API_KEY/TAVILY_API_KEY를 "
        "설정하고, 환경변수 RUN_LIVE_AI_TESTS=1 로 실행해야 동작합니다 "
        "(비용·시간이 발생하므로 기본값은 skip 입니다)."
    ),
)

skip_unless_live_rag = pytest.mark.skipif(
    not (RUN_LIVE_AI_TESTS and _live_agent_configured() and _ollama_ready()),
    reason=(
        "내부 지식(RAG) 테스트입니다. RUN_LIVE_AI_TESTS=1, GROQ/TAVILY 키 설정에 더해 "
        f"로컬 Ollama 서버와 임베딩 모델({EMBEDDING_MODEL}) 준비가 필요합니다."
    ),
)


# ── 테스트 시나리오(TS)별 결과 요약 출력 ────────────────────────────────
# 테스트 파일명이 test_ts01_..., test_ts02_... 처럼 TS ID를 담고 있으므로,
# 파일명에서 TS ID를 뽑아 pytest 실행이 끝날 때마다 'TS 목록' 시트와 같은
# 순서로 Pass/Fail/Skip 개수를 표로 보여준다(테스트시나리오_테스트결과.xlsx > TS 목록 참고).
_TS_FILE_PATTERN = re.compile(r"test_ts(\d{2})_")

_TS_NAMES = {
    "01": "건강고민을 입력해 맞춤 상품을 추천받는다",
    "02": "상품상세에서 성분을 쉬운 설명으로 확인한다",
    "03": "AI상담에서 내부 지식(RAG)으로 질문에 답한다",
    "04": "AI상담에서 외부 뉴스를 조회해 답한다",
    "05": "AI상담이 회수·경보를 발견하면 CS 연결을 권장한다",
    "06": "AI상담이 모호하거나 근거 없는 질문에 안전하게 대응한다",
    "07": "AI상담에 개인정보·금지 요청을 입력했을 때 안전하게 처리한다",
    "08": "AI상담 관련 설정이 준비되지 않았을 때 오류를 명확히 안내한다",
    "09": "여러 상품을 함께 담았을 때 과다섭취를 경고한다",
    "10": "잘못된 입력·존재하지 않는 데이터를 조회했을 때 오류를 안내한다",
}


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """`uv run pytest`를 실행할 때마다 TS별 Pass/Fail/Skip 개수를 표로 출력한다.

    pytest 자체 요약(예: '13 passed, 10 skipped')은 전체 개수만 보여주지만,
    이 표는 'TS 목록' 시트의 TS 단위로 묶어서 어떤 시나리오가 통과/실패/스킵인지
    바로 보이게 한다. 별도 옵션 없이 `pytest`만 실행해도 항상 함께 출력된다.
    """
    from collections import defaultdict

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})

    for outcome in ("passed", "failed", "skipped"):
        for report in terminalreporter.stats.get(outcome, []):
            # 'call' 단계 결과만 센다. 단, skip은 보통 setup 단계에서 결정되므로 함께 포함한다.
            if report.when not in ("call", "setup"):
                continue
            if outcome != "skipped" and report.when != "call":
                continue
            match = _TS_FILE_PATTERN.search(report.nodeid)
            if not match:
                continue
            counts[match.group(1)][outcome] += 1

    if not counts:
        return

    terminalreporter.write_sep("=", "테스트 시나리오(TS)별 결과 요약")
    for ts_num in sorted(counts):
        c = counts[ts_num]
        total = c["passed"] + c["failed"] + c["skipped"]
        if c["failed"] > 0:
            mark = "FAIL"
        elif c["skipped"] == total:
            mark = "SKIP"
        else:
            mark = "PASS"
        name = _TS_NAMES.get(ts_num, "")
        line = (
            f"TS-{ts_num}  [{mark:>4}]  Pass {c['passed']} / Fail {c['failed']} / "
            f"Skip {c['skipped']}  (총 {total}건)  - {name}"
        )
        terminalreporter.write_line(line)
