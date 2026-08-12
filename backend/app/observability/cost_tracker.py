# ===== app/observability/cost_tracker.py =====
from app.core.config import settings

def estimate_llm_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * settings.LLM_INPUT_COST_PER_1K + \
           (output_tokens / 1000) * settings.LLM_OUTPUT_COST_PER_1K

def estimate_embedding_cost(token_count: int) -> float:
    return (token_count / 1000) * settings.EMBEDDING_COST_PER_1K
