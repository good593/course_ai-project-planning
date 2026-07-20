# -*- coding: utf-8 -*-
"""TS-03: AI상담에서 내부 지식(RAG)으로 질문에 답한다.

관련 API: POST /chat (search_internal_knowledge)
대상 TC: TC-006, TC-007, TC-008

주의: 이 파일의 테스트는 실제 GROQ LLM 호출과 로컬 Ollama 임베딩(RAG 검색)을
사용하므로 비용·시간이 발생한다. 아래 조건을 모두 만족해야 실행된다.
  1) backend/.env 에 GROQ_API_KEY / TAVILY_API_KEY 설정
  2) 로컬에서 `ollama serve` 실행 + 임베딩 모델 pull 완료
  3) 환경변수 RUN_LIVE_AI_TESTS=1 로 실행 (기본은 skip)

AI 응답의 '내용'(정확성/완결성/명확성 등)은 사람이 'AI 응답 평가 척도'
시트의 1~5점으로 채점해야 한다. 이 테스트는 그중 기계적으로 확인 가능한
부분(상태 코드, 근거 라벨 존재 여부, 외부 Tool 미사용 여부, 반복 응답의
핵심 근거 일관성)만 자동 검증한다.
"""
import pytest

from conftest import skip_unless_live_rag


@skip_unless_live_rag
def test_tc006_internal_knowledge_only_answer(client):
    """TC-006: 내부 지식(RAG)만으로 답변 가능한 질문에는 search_internal_knowledge만 사용된다."""
    response = client.post(
        "/chat", json={"message": "루테인이 어떤 성분이야?", "history": []}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["answer"], "빈 답변은 통과로 볼 수 없다."
    assert len(data["참고_문서_목록"]) >= 1, "내부 지식베이스 근거 라벨이 노출되어야 한다."
    assert data["출처_URL_목록"] == [], "내부 지식만으로 답할 수 있으면 외부 Tool을 쓰지 않아야 한다."

    print(f"\n[TC-006 answer]\n{data['answer']}")
    print(f"[TC-006 참고_문서_목록] {data['참고_문서_목록']}")


@skip_unless_live_rag
def test_tc007_age_specific_intake_standard_answer(client):
    """TC-007: 연령대별 섭취기준(임산부 엽산) 질문에 DB 기준 수치와 출처를 안내한다.

    DB 기준: 영양소_섭취기준(엽산, 임산부, 여성) 권장섭취량 = 620 μg DFE.
    LLM이 표현을 바꿔 말할 수 있으므로 숫자 자체는 참고용으로만 출력하고,
    하드 assert는 '근거 문서가 함께 제시되었는가'로 제한한다.
    """
    response = client.post(
        "/chat", json={"message": "임산부는 엽산을 얼마나 먹어야 해?", "history": []}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["answer"]
    assert len(data["참고_문서_목록"]) >= 1

    contains_expected_number = "620" in data["answer"]
    print(f"\n[TC-007 answer]\n{data['answer']}")
    print(f"[TC-007 참고_문서_목록] {data['참고_문서_목록']}")
    if not contains_expected_number:
        print(
            "[TC-007 참고] 응답에 DB 기준 수치(620)가 그대로 보이지 않습니다. "
            "표현이 달라졌을 수 있으니 'AI 응답 평가 척도'로 사람이 확인해주세요."
        )


@skip_unless_live_rag
def test_tc008_repeated_question_has_consistent_core_evidence(client):
    """TC-008: 같은 질문을 새 대화로 3회 반복해도 핵심 근거(참고 문서)는 동일해야 한다.

    표현(문장)은 매번 달라질 수 있지만, RAG 검색은 같은 질문에 대해
    같은 top-k 문서를 반환하는 것이 정상이므로 참고_문서_목록 집합을 비교한다.
    """
    reference_sets = []
    answers = []
    for _ in range(3):
        response = client.post(
            "/chat", json={"message": "루테인이 어떤 성분이야?", "history": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        reference_sets.append(frozenset(data["참고_문서_목록"]))
        answers.append(data["answer"])

    print("\n[TC-008 3회 응답]")
    for i, ans in enumerate(answers, 1):
        print(f"--- {i}회차 ---\n{ans}")

    assert reference_sets[0] == reference_sets[1] == reference_sets[2], (
        "3회 응답의 핵심 근거(참고_문서_목록)가 서로 달라 일관성 기준을 만족하지 못했습니다: "
        f"{reference_sets}"
    )
