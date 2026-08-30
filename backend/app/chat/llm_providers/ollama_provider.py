# ===== app/chat/llm_providers/ollama_provider.py =====

from typing import AsyncIterator
from langchain_ollama import ChatOllama
from app.chat.llm_providers.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging_config import logger

class OllamaLLMProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(self, model: str = None):
        self.model_name = model or settings.LLM_MODEL
        headers = {"Authorization": f"Bearer {settings.OLLAMA_URL}"} if settings.OLLAMA_URL else None
        client_kwargs = {"headers": headers} if headers else None
        self._llm = ChatOllama(model=self.model_name, base_url=settings.OLLAMA_URL, num_ctx=settings.LLM_MAX_CONTEXT_TOKENS, temperature=0.1, client_kwargs=client_kwargs)

    async def generate(self, prompt: str) -> str:
        try:
            result = await self._llm.ainvoke(prompt)
            return result.content
        except Exception as e:
            logger.warning("ollama_generate_failed_offline", error=str(e))
            return "I don't have enough information in the documents to answer this."

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        try:
            async for chunk in self._llm.astream(prompt):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.warning("ollama_stream_failed_offline", error=str(e))
            yield "I don't have enough information in the documents to answer this."