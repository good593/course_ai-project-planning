"""LLM 모델별 토큰 단가 테이블.

"AI 서비스 운영 및 비용 관리.md"가 강조하듯, 실제 단가는 제공업체가 수시로
바꾸므로 코드 곳곳에 흩어두지 않고 이 파일 하나에 모아 학생/운영자가
쉽게 최신값으로 갱신할 수 있게 한다.

주의: 아래 단가는 예시값이다. 실습 전에 반드시 GROQ 콘솔의 최신 가격표
(https://groq.com/pricing)를 확인하고 실제 값으로 바꿔서 사용해야 한다.
"""

# 모델명 -> (입력 100만 토큰당 USD, 출력 100만 토큰당 USD)
# 아래 값은 2026-07 시점에 참고한 예시 단가이며, 실제 운영 전 최신 가격표로 반드시 갱신할 것.
MODEL_PRICING_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-120b": (0.15, 0.75),
    "openai/gpt-oss-20b": (0.10, 0.50),
    "llama-3.1-8b-instant": (0.05, 0.08),
    "llama-3.3-70b-versatile": (0.59, 0.79),
}

# 가격표에 없는 모델(신규/오타 등)은 비용을 0으로 두어 "단가 미확인" 상태를 드러낸다.
# 조용히 잘못된 값을 계산하는 것보다, 0으로 표시해서 사람이 pricing.py를 갱신하도록 유도한다.
_UNKNOWN_MODEL_PRICE = (0.0, 0.0)


def calc_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """입력/출력 토큰 수와 모델 단가로 예상 비용(USD)을 계산한다.

    공식(강의자료 '비용 산정의 기본식'): 비용 = 토큰 수 × 모델 단가.
    """
    input_price, output_price = MODEL_PRICING_PER_1M_TOKENS.get(model, _UNKNOWN_MODEL_PRICE)
    return (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price


def is_price_known(model: str) -> bool:
    """단가표에 등록된 모델인지 확인한다. False면 cost_usd=0이 '무료'가 아니라 '단가 미확인'임을 뜻한다."""
    return model in MODEL_PRICING_PER_1M_TOKENS
