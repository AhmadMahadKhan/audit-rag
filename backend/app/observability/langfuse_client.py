# ===== app/observability/langfuse_client.py =====
"""LLM-specific observability — separate from generic OTel traces since
Langfuse understands prompts/tokens/RAG structure natively."""
from app.core.config import settings

_client = None

def get_langfuse():
    global _client
    if _client is None and settings.LANGFUSE_PUBLIC_KEY:
        from langfuse import Langfuse
        _client = Langfuse(public_key=settings.LANGFUSE_PUBLIC_KEY, secret_key=settings.LANGFUSE_SECRET_KEY,
                            host=settings.LANGFUSE_HOST)
    return _client

def log_llm_generation(name: str, model: str, prompt: str, response: str, input_tokens: int,
                        output_tokens: int, latency_ms: float, user_id: str | None = None):
    client = get_langfuse()
    if not client:
        return  # Langfuse optional — no-op if not configured
    trace = client.trace(name=name, user_id=user_id)
    trace.generation(name=name, model=model, input=prompt[:2000], output=response[:2000],
                      usage={"input": input_tokens, "output": output_tokens},
                      metadata={"latency_ms": latency_ms})