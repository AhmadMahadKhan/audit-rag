# ===== app/chat/llm_providers/ollama_provider.py =====

from typing import AsyncIterator
from langchain_ollama import ChatOllama
from app.chat.llm_providers.base import BaseLLMProvider
from app.core.config import settings

class OllamaLLMProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(self, model: str = None):
        self.model_name = model or settings.LLM_MODEL
        headers = {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"} if settings.OLLAMA_API_KEY else None
        client_kwargs = {"headers": headers} if headers else None
        self._llm = ChatOllama(model=self.model_name, base_url=settings.OLLAMA_URL, temperature=0.1, client_kwargs=client_kwargs)

    async def generate(self, prompt: str) -> str:
        result = await self._llm.ainvoke(prompt)
        return result.content

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        async for chunk in self._llm.astream(prompt):
            if chunk.content:
                yield chunk.content