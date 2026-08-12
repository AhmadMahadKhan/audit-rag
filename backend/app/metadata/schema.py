from pydantic import BaseModel

class MetadataField(BaseModel):
    key: str
    value: str
    category: str  # document | business | financial | processing
    confidence: float
    extractor: str

METADATA_CATEGORIES = {"document", "business", "financial", "processing"}