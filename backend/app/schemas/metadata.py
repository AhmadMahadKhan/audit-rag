# ===== app/schemas/metadata.py =====
from pydantic import BaseModel
from datetime import datetime

class MetadataFieldOut(BaseModel):
    key: str
    value: str
    category: str
    confidence: float
    extractor: str
    status: str

    class Config:
        from_attributes = True

class MetadataUpdateRequest(BaseModel):
    key: str
    value: str

class MetadataSearchRequest(BaseModel):
    filters: dict[str, str]
    skip: int = 0
    limit: int = 50

class ExtractionRunOut(BaseModel):
    id: str
    document_id: str
    overall_confidence: float
    status: str
    field_count: int
    low_confidence_count: int
    created_at: datetime

    class Config:
        from_attributes = True