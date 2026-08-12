# ===== app/chat/token_budget.py =====
from app.chunking.token_utils import estimate_tokens

def fit_context_to_budget(chunks: list[dict], max_tokens: int) -> list[dict]:
    """Greedily includes chunks (already ranked best-first) until budget is hit."""
    budget = max_tokens
    selected = []
    for c in chunks:
        t = estimate_tokens(c["content"])
        if t > budget:
            break
        selected.append(c)
        budget -= t
    return selected

def trim_history(history: list[dict], max_tokens: int) -> list[dict]:
    kept, budget = [], max_tokens
    for m in reversed(history):
        t = estimate_tokens(m["content"])
        if t > budget:
            break
        kept.insert(0, m)
        budget -= t
    return kept