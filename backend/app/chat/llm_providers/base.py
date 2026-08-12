# ===== app/chat/llm_providers/base.py =====
from abc import ABC, abstractmethod
from typing import AsyncIterator

class BaseLLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str: ...

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...
