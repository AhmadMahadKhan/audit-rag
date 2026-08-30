# ===== app/models/audit_agent.py =====
from sqlalchemy import String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class AuditRun(BaseModel):
    __tablename__ = "audit_runs"
    name: Mapped[str] = mapped_column(String)
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    document_ids: Mapped[list] = mapped_column(JSON)  # resolved list, even if request said "all"
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|completed|failed
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str] = mapped_column(String, nullable=True)
    error_message: Mapped[str] = mapped_column(String, nullable=True)

class AuditMemorySnapshot(BaseModel):
    """One row per document processed — lets you inspect the running memory
    trail after the fact, not just the final report."""
    __tablename__ = "audit_memory_snapshots"
    run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id"), index=True)
    document_id: Mapped[str] = mapped_column(String, index=True)
    order_index: Mapped[int] = mapped_column(Integer)
    document_summary: Mapped[str] = mapped_column(Text)
    map_batches_used: Mapped[int] = mapped_column(Integer, default=1)  # 1 = no map/reduce needed
    memory_after: Mapped[dict] = mapped_column(JSON)  # full memory JSON snapshot at this point
    memory_compacted: Mapped[bool] = mapped_column(default=False)  # True if compaction ran after this doc

class AuditReport(BaseModel):
    __tablename__ = "audit_reports"
    run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id"), unique=True, index=True)
    content_markdown: Mapped[str] = mapped_column(Text)
    risk_summary: Mapped[dict] = mapped_column(JSON, default=dict)  # {critical: n, high: n, medium: n, low: n}
    documents_covered: Mapped[int] = mapped_column(Integer, default=0)
    documents_failed: Mapped[int] = mapped_column(Integer, default=0)