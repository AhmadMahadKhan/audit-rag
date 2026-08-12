# ===== app/reranking/factory.py =====
from app.reranking.cross_encoder_provider import CrossEncoderReranker
from app.reranking.base import BaseReranker
from app.core.config import settings

_cache: dict[str, BaseReranker] = {}

def get_reranker(name: str | None = None) -> BaseReranker:
    provider_name = name or settings.RERANKER_PROVIDER
    if provider_name in _cache:
        return _cache[provider_name]
    if provider_name == "sentence_transformers":
        reranker = CrossEncoderReranker()
    elif provider_name == "jina":
        from app.reranking.jina_provider import JinaReranker
        reranker = JinaReranker()
    else:
        raise ValueError(f"Unknown reranker provider: {provider_name}")
    _cache[provider_name] = reranker
    return reranker