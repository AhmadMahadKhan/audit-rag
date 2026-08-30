# ===== app/audit_agent/batching.py =====
"""Splits document content into token-budgeted batches for the map step —
distinct from chat's fit_context_to_budget(), which truncates rather than
batches everything."""
from app.chunking.token_utils import estimate_tokens

def batch_texts_by_budget(texts: list[str], max_tokens: int) -> list[list[str]]:
    if not texts:
        return [[]]
    batches: list[list[str]] = []
    current: list[str] = []
    current_tokens = 0
    for t in texts:
        t_tokens = estimate_tokens(t)
        if current and current_tokens + t_tokens > max_tokens:
            batches.append(current)
            current, current_tokens = [], 0
        current.append(t)
        current_tokens += t_tokens
    if current:
        batches.append(current)
    return batches
