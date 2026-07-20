# -*- coding: utf-8 -*-
"""TS-11: LLM 호출마다 토큰 사용량/비용이 자동으로 기록된다.

관련 모듈: app/services/usage_service.py (track_usage)

실제 GROQ API를 호출하지 않고, LangChain의 FakeMessagesListChatModel(진짜
BaseChatModel 구현체)이 usage_metadata가 담긴 AIMessage를 반환하게 만들어
콜백 체인(on_llm_end -> get_usage_metadata_callback)이 실제로 동작하는지까지
검증한다. 네트워크 호출이 없으므로 비용·시간이 들지 않고, RUN_LIVE_AI_TESTS도
필요 없다.
"""
from app.core.database import SessionLocal
from app.core.pricing import calc_cost_usd
from app.models.usage_log import UsageLog
from app.services import usage_service


def _fake_message(model_name: str, input_tokens: int, output_tokens: int):
    from langchain_core.messages import AIMessage

    return AIMessage(
        content="테스트 응답",
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
        response_metadata={"model_name": model_name},
    )


def _fake_chat_model(model_name: str, input_tokens: int, output_tokens: int):
    """usage_metadata가 채워진 AIMessage를 반환하는 가짜 ChatModel을 만든다."""
    from langchain_core.language_models import FakeMessagesListChatModel

    return FakeMessagesListChatModel(
        responses=[_fake_message(model_name, input_tokens, output_tokens)]
    )


def _latest_log() -> UsageLog:
    db = SessionLocal()
    try:
        return db.query(UsageLog).order_by(UsageLog.id.desc()).first()
    finally:
        db.close()


def test_llm_call_records_usage_row(usage_log_cleanup):
    """track_usage 블록 안에서 LLM을 1회 호출하면 토큰/비용이 정확히 기록된다."""
    llm = _fake_chat_model("test-model-ts11-a", input_tokens=120, output_tokens=40)

    with usage_service.track_usage(feature="chat") as usage:
        llm.invoke("안녕하세요")
        usage.tool_call_count = 2

    row = _latest_log()
    assert row is not None
    assert row.feature == "chat"
    assert row.model == "test-model-ts11-a"
    assert row.input_tokens == 120
    assert row.output_tokens == 40
    assert row.total_tokens == 160
    assert row.tool_call_count == 2
    assert row.success is True
    assert row.error_message is None
    assert row.cost_usd == calc_cost_usd("test-model-ts11-a", 120, 40)


def test_llm_call_failure_is_recorded_as_failed(usage_log_cleanup):
    """블록 안에서 예외가 나면 실패로 기록하고, 예외는 삼키지 않고 그대로 전파한다."""
    raised = False
    try:
        with usage_service.track_usage(feature="chat"):
            raise RuntimeError("가짜 LLM 오류")
    except RuntimeError:
        raised = True

    assert raised, "예외가 삼켜지지 않고 호출자에게 전파되어야 한다."

    row = _latest_log()
    assert row is not None
    assert row.success is False
    assert row.error_message is not None and "가짜 LLM 오류" in row.error_message
    assert row.model == "unknown", "LLM이 한 번도 응답하지 못했으므로 모델을 특정할 수 없어야 한다."


def test_multiple_calls_in_one_request_are_aggregated_per_model(usage_log_cleanup):
    """Tool 호출 루프처럼 한 요청 안에서 LLM이 여러 번 불려도 모델별로 합산된 행 1개만 남는다."""
    from langchain_core.language_models import FakeMessagesListChatModel

    llm = FakeMessagesListChatModel(
        responses=[
            _fake_message("test-model-ts11-b", input_tokens=50, output_tokens=10),
            _fake_message("test-model-ts11-b", input_tokens=30, output_tokens=5),
        ]
    )

    with usage_service.track_usage(feature="chat"):
        llm.invoke("첫 번째 호출")
        llm.invoke("두 번째 호출(Tool 결과를 반영한 재호출 상황을 흉내)")

    row = _latest_log()
    assert row is not None
    assert row.model == "test-model-ts11-b"
    assert row.input_tokens == 50 + 30
    assert row.output_tokens == 10 + 5
    assert row.total_tokens == 60 + 35
