# ===== app/schemas/dashboard.py =====
from pydantic import BaseModel
from datetime import datetime

class StatCard(BaseModel):
    label: str
    value: float
    unit: str | None = None
    trend_pct: float | None = None
    status: str = "ok"  # ok, warning, critical
    updated_at: datetime

class DashboardSummary(BaseModel):
    total_documents: StatCard
    documents_processed: StatCard
    processing_queue: StatCard
    failed_documents: StatCard
    ocr_success_rate: StatCard
    storage_usage: StatCard
    embedding_count: StatCard
    active_users: StatCard

class ActivityItem(BaseModel):
    id: str
    event_type: str
    status: str
    user_email: str | None
    related_document_id: str | None
    created_at: datetime

class ServiceStatus(BaseModel):
    name: str
    status: str  # up, down, degraded
    latency_ms: float | None = None

class SystemHealth(BaseModel):
    services: list[ServiceStatus]
    overall: str

class ChartPoint(BaseModel):
    label: str
    value: float

class ChartSeries(BaseModel):
    name: str
    points: list[ChartPoint]