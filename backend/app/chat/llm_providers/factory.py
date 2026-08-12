# ===== app/chat/llm_providers/factory.py =====
from app.chat.llm_providers.ollama_provider import OllamaLLMProvider
from app.chat.llm_providers.base import BaseLLMProvider
from app.core.config import settings

_cache: dict[str, BaseLLMProvider] = {}

def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    provider_name = name or settings.LLM_PROVIDER
    if provider_name in _cache:
        return _cache[provider_name]
    if provider_name == "ollama":
        provider = OllamaLLMProvider()
    elif provider_name == "openai":
        from app.chat.llm_providers.openai_provider import OpenAILLMProvider
        provider = OpenAILLMProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
    _cache[provider_name] = provider
    return provider
