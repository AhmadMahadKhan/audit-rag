
# ===== app/chunking/base.py =====
from abc import ABC, abstractmethod
from app.canonical.schema import CanonicalDocument
from app.chunking.schema import ChunkCandidate

class BaseChunker(ABC):
    name: str = "base"
    max_tokens: int = 500
    overlap_tokens: int = 50

    @abstractmethod
    def chunk(self, doc: CanonicalDocument) -> list[ChunkCandidate]: ...
