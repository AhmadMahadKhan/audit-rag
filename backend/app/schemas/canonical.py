from pydantic import BaseModel
from datetime import datetime

class CanonicalOut(BaseModel):
    id: str
    document_id: str
    schema_version: str
    validation_status: str
    validation_issues: list[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CanonicalDetailOut(CanonicalOut):
    canonical_json: dict