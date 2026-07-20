# backend 테스트 안내

전체 개요는 [test/README.md](../README.md)를 먼저 보세요. 이 문서는
RF-3(AI상담) 라이브 테스트(TC-006~TC-015)를 실행하는 방법만 자세히 다룹니다.

## 기본 실행 (비용 없음, 몇 초 소요)

```bash
cd backend
uv run pytest -v
```

TC-006~015는 아래처럼 skip 이유가 함께 출력됩니다.

```
test_ts03_rag_chat.py::test_tc006_internal_knowledge_only_answer SKIPPED
  (내부 지식(RAG) 테스트입니다. RUN_LIVE_AI_TESTS=1, GROQ/TAVILY 키 설정에 더해
   로컬 Ollama 서버와 임베딩 모델(...) 준비가 필요합니다.)
```

## 라이브 AI 테스트 실행 (실제 GROQ/Tavily 호출, 비용·시간 발생)

### 준비물

1. `backend/.env` 에 `GROQ_API_KEY`, `TAVILY_API_KEY` 설정
2. TC-006~008 (내부 지식/RAG)을 실행하려면 추가로:
   - 로컬에서 `ollama serve` 실행 중
   - `ollama pull <EMBEDDING_MODEL>` 로 `backend/.env`의 `EMBEDDING_MODEL`
     (기본값: `qwen3-embedding:0.6b`)을 미리 받아둘 것
   - 아래 명령으로 준비 상태를 먼저 확인할 수 있습니다.
     ```bash
     curl http://localhost:11434/api/tags
     ```

### 실행

```bash
# Windows PowerShell — 전체(TC-006~015 포함) 실행
$env:RUN_LIVE_AI_TESTS = "1"
uv run pytest -v --junitxml=../test/backend/results.xml

# TS 하나만 실행하고 싶다면 -k 로 좁혀서 실행 (TS별 명령어는 test/README.md 표 참고)
$env:RUN_LIVE_AI_TESTS = "1"
uv run pytest -v -k ts06

# 라이브 AI 테스트 전체(TC-006~015)만 모아서 실행 (파일명이 전부 *_chat.py 라서 가능)
$env:RUN_LIVE_AI_TESTS = "1"
uv run pytest -v -k "chat" --junitxml=../test/backend/results.xml
```

- TC-006~008은 `skip_unless_live_rag` 마커가 붙어 있어 Ollama/임베딩 모델까지
  준비되어야 실행됩니다. GROQ/TAVILY 키만 있고 Ollama가 없다면 이 3개만 계속
  skip되고 나머지(TC-009~015)는 실행됩니다.
- 각 라이브 테스트는 `print()`로 실제 `answer`, `참고_문서_목록`,
  `출처_URL_목록`, `cs_상담_권장` 값을 출력합니다(`-v`만으로는 안 보이고, 통과한
  테스트의 print는 기본적으로 숨겨지므로 `-s` 를 더하면 항상 볼 수 있습니다:
  `uv run pytest -v -s -k ts06`). `--junitxml` 로 저장하면(pyproject.toml에
  `junit_logging = "all"` 설정되어 있어) 이 출력이 결과 XML의 `<system-out>`
  에도 그대로 남으므로, 나중에 다시 열어볼 수 있습니다.

### 실제 출력 예시 (TC-006, `-s` 옵션으로 print 내용까지 표시)

```bash
$ uv run pytest -v -s -k tc006
```
```
test_ts03_rag_chat.py::test_tc006_internal_knowledge_only_answer
[TC-006 answer]
루테인(Lutein)은 눈 건강을 지원하는 기능성 원료입니다.
- 눈의 피로를 완화하고, 황반색소 밀도를 유지해 시력 보호에 도움을 줍니다.
- 식품의약품안전처가 인정한 건강기능식품 기능성 근거에 따라 "눈 건강"을 주요 효능으로 인정받고 있습니다.
※ 근거: [근거 1] 영양소_기능성_추천DB – 루테인 (식품의약품안전처 고시)
[TC-006 참고_문서_목록] ['영양소_기능성_추천DB - 루테인']
PASSED

============================= 테스트 시나리오(TS)별 결과 요약 =============================
TS-03  [PASS]  Pass 1 / Fail 0 / Skip 0  (총 1건)  - AI상담에서 내부 지식(RAG)으로 질문에 답한다
================================ 1 passed in 12.87s ================================
```

이 `answer` 내용을 그대로 복사해서 'AI 응답 평가 척도' 시트 기준으로 채점하면 됩니다.

### ⚠️ `assert 502 == 200`으로 실패한다면

대부분 코드 버그가 아니라 **GROQ API 무료 티어의 일일 토큰 한도(TPD) 소진**입니다.
`app/routers/chat.py`가 LLM 호출 실패(`AgentError`)를 502로 감싸서 안내하도록
만들어져 있는데, 그 로직이 정상 동작한 것뿐입니다. 라이브 테스트를 반복해서 여러 번
돌릴수록 토큰을 빠르게 소모하므로, TC-006~015 여러 개를 자주 재실행하면 겪을 수 있습니다.

원인을 직접 확인하려면:

```bash
uv run python -c "from app.services import agent_service; agent_service.ask('테스트', [])"
```

에러 메시지에 `rate_limit_exceeded` / `tokens per day`가 보이면 한도 소진이 맞습니다.
해결책은 코드 수정이 아니라 **기다리는 것**입니다(몇 분~다음날). 반복 실행이 잦다면
전체를 매번 돌리지 말고 `-k`로 필요한 TC만 좁혀서 토큰을 아끼세요. 이 상태로
`export_results_to_excel.py`를 돌리면 진짜 결함이 아닌데 'Fail'로 기록되니,
한도 소진이 의심되면 엑셀 반영 전에 원인부터 확인하세요.

## 실행 후 사람이 해야 할 일

라이브 테스트는 "형식이 맞는가/금지된 내용이 없는가"까지만 자동 검증합니다.
아래는 반드시 사람이 `테스트시나리오_테스트결과.xlsx`를 열어 직접 채워야 합니다.

1. 각 TC의 실제 `answer` 내용을 읽고 'AI 응답 평가 척도' 시트의 1~5점 기준으로
   'TC 상세' 시트의 '평가 점수(1~5)' 열을 채운다.
2. 3점 이하이거나 Fail인 케이스는 '결함 기록' 시트에 TC ID를 연결해 재현 조건과
   함께 기록한다(DF-001 예시 참고).

`test/export_results_to_excel.py` 는 Pass/Fail/Skip 여부만 자동으로 채우고,
'평가 점수(1~5)' 열은 항상 비워둡니다(사람이 채우는 열이기 때문).
