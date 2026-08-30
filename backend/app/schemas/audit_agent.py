# ===== app/schemas/audit_agent.py =====
from pydantic import BaseModel
from datetime import datetime

class StartAuditRequest(BaseModel):
    name: str
    document_ids: list[str] | None = None  # None/empty = every document you're authorized to see

class AuditRunOut(BaseModel):
    id: str
    name: str
    status: str
    progress_current: int
    progress_total: int
    current_stage: str | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditSnapshotOut(BaseModel):
    document_id: str
    order_index: int
    document_summary: str
    map_batches_used: int
    memory_compacted: bool

    class Config:
        from_attributes = True

class AuditReportOut(BaseModel):
    run_id: str
    content_markdown: str
    risk_summary: dict
    documents_covered: int
    documents_failed: int

    class Config:
        from_attributes = True