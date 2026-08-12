from abc import ABC, abstractmethod
from app.parsing.schema import ParsedDocument

class BaseParser(ABC):
    name: str = "base"
    version: str = "1.0"

    @abstractmethod
    async def parse(self, document_id: str, content: bytes) -> ParsedDocument: ...
