
# ===== app/embeddings/factory.py =====
from app.embeddings.ollama_provider import OllamaEmbeddingProvider
from app.embeddings.sentence_transformers_provider import SentenceTransformersProvider
from app.embeddings.base import BaseEmbeddingProvider
from app.core.config import settings

_PROVIDER_CACHE: dict[str, BaseEmbeddingProvider] = {}

def get_embedding_provider(name: str | None = None) -> BaseEmbeddingProvider:
    provider_name = name or settings.EMBEDDING_PROVIDER
    if provider_name in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[provider_name]

    if provider_name == "ollama":
        provider = OllamaEmbeddingProvider()
    elif provider_name == "sentence_transformers":
        provider = SentenceTransformersProvider()
    elif provider_name == "openai":
        from app.embeddings.openai_provider import OpenAIEmbeddingProvider
        provider = OpenAIEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {provider_name}")

    _PROVIDER_CACHE[provider_name] = provider
    return provider