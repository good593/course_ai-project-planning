# -*- coding: utf-8 -*-
"""TS-05: AI상담이 회수·경보를 발견하면 CS 연결을 권장한다(Human-in-the-loop).

관련 API: POST /chat (search_recall_alert)
대상 TC: TC-010

실제 GROQ/Tavily 호출이 발생하므로 RUN_LIVE_AI_TESTS=1 로 실행할 때만 동작한다.
(자세한 내용은 test_ts03_rag_chat.py 상단 설명 참고)

주의: '회수 이력이 실제로 검색되는가'는 그날그날의 실제 뉴스/공공기관 데이터에
좌우되는 외부 의존 요소다. 따라서 cs_상담_권장=True를 강제로 단정하지 않고,
'회수·경보가 발견되면 반드시 자동 연결 없이 버튼만 노출된다'는 정책(자동 연결 금지)을
중심으로 검증한다. 실제로 회수 이력이 잡혔는지는 사람이 answer를 보고 확인해야 한다.
"""
from conftest import skip_unless_live_ai


@skip_unless_live_ai
def test_tc010_recall_alert_triggers_human_in_the_loop(client):
    """TC-010: 회수·부작용 이력 질문에 자동 연결 없이 CS 상담 연결 권장 여부만 안내한다."""
    response = client.post(
        "/chat",
        json={"message": "홍삼정 리미티드 스틱 제품 회수된 적 있어?", "history": []},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["answer"]
    assert isinstance(data["cs_상담_권장"], bool)

    # 정책 검증: cs_상담_권장이 True라면(=회수/경보가 실제로 발견되었다면)
    # 출처 URL도 함께 있어야 하고, 답변 자체가 자동으로 상담을 연결했다는
    # 문구(예: '연결해드렸습니다')를 포함해서는 안 된다(직접 연결 금지, 버튼만 노출).
    if data["cs_상담_권장"]:
        assert len(data["출처_URL_목록"]) >= 1
        forbidden_phrases = ["연결해드렸습니다", "바로 연결했습니다", "자동으로 연결"]
        for phrase in forbidden_phrases:
            assert phrase not in data["answer"], (
                f"자동 연결을 암시하는 문구가 포함되어 있습니다(Human-in-the-loop 위반): {phrase}"
            )

    print(f"\n[TC-010 answer]\n{data['answer']}")
    print(f"[TC-010 cs_상담_권장] {data['cs_상담_권장']}")
    print(f"[TC-010 출처_URL_목록] {data['출처_URL_목록']}")
    print(
        "[TC-010 참고] 이 제품에 실제 회수 이력이 있는지는 외부 데이터에 따라 달라집니다. "
        "cs_상담_권장 값과 answer 내용을 사람이 최종 확인해주세요."
    )
