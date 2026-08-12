
# ===== app/schemas/classification.py =====
from pydantic import BaseModel
from datetime import datetime

class ClassificationOut(BaseModel):
    id: str
    document_id: str
    document_type: str
    confidence: float
    method: str
    pipeline: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReclassifyRequest(BaseModel):
    document_type: str | None = None  # if provided, manual override; else re-run classifier
