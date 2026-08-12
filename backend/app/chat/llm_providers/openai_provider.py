# ===== app/chat/llm_providers/openai_provider.py =====
"""Optional — requires OPENAI_API_KEY. Uses LangChain's OpenAI wrapper for interface parity."""
from typing import AsyncIterator
from app.chat.llm_providers.base import BaseLLMProvider
from app.core.config import settings

class OpenAILLMProvider(BaseLLMProvider):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini"):
        from langchain_openai import ChatOpenAI
        if not getattr(settings, "OPENAI_API_KEY", None):
            raise ValueError("OPENAI_API_KEY not configured")
        self.model_name = model
        self._llm = ChatOpenAI(model=model, api_key=settings.OPENAI_API_KEY, temperature=0.1)

    async def generate(self, prompt: str) -> str:
        result = await self._llm.ainvoke(prompt)
        return result.content

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        async for chunk in self._llm.astream(prompt):
            if chunk.content:
                yield chunk.content