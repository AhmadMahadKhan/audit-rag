from abc import ABC, abstractmethod
from app.canonical.schema import CanonicalDocument
from app.metadata.schema import MetadataField

class BaseExtractor(ABC):
    name: str = "base"
    version: str = "1.0"

    @abstractmethod
    def extract(self, doc: CanonicalDocument) -> list[MetadataField]: ...