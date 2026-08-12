# ===== app/models/monitoring.py =====
from sqlalchemy import String, Float, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class ErrorEvent(BaseModel):
    __tablename__ = "error_events"
    exception_type: Mapped[str] = mapped_column(String, index=True)
    message: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, index=True)  # validation|auth|parsing|ocr|db|storage|retrieval|embedding|llm|network|config|internal
    service: Mapped[str] = mapped_column(String, nullable=True)
    endpoint: Mapped[str] = mapped_column(String, nullable=True)
    request_id: Mapped[str] = mapped_column(String, nullable=True)
    trace_id: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[str] = mapped_column(String, nullable=True)
    stack_trace: Mapped[str] = mapped_column(String, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String, index=True)  # groups repeated errors
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)

class LLMUsageEvent(BaseModel):
    __tablename__ = "llm_usage_events"
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)  # chat|embed|rerank|classify|extract
    user_id: Mapped[str] = mapped_column(String, nullable=True)
    document_id: Mapped[str] = mapped_column(String, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    time_to_first_token_ms: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="success")

class AlertRule(BaseModel):
    __tablename__ = "alert_rules"
    name: Mapped[str] = mapped_column(String, unique=True)
    metric_name: Mapped[str] = mapped_column(String)
    condition: Mapped[str] = mapped_column(String)  # gt|lt|eq
    threshold: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String)  # critical|high|medium
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_channel: Mapped[str] = mapped_column(String, nullable=True)

class AlertEvent(BaseModel):
    __tablename__ = "alert_events"
    rule_id: Mapped[str] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    rule_name: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    metric_value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="firing")  # firing|acknowledged|resolved
    acknowledged_by: Mapped[str] = mapped_column(String, nullable=True)