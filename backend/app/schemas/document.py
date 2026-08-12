# ===== app/schemas/document.py =====
from pydantic import BaseModel
from datetime import datetime

class DocumentOut(BaseModel):
    id: str
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class UploadResult(BaseModel):
    filename: str
    document_id: str | None
    status: str
    error: str | None = None

class UploadBatchResponse(BaseModel):
    results: list[UploadResult]
    success_count: int
    failure_count: int
