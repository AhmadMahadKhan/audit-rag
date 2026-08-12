# ===== app/models/rule_engine.py =====
from sqlalchemy import String, Float, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class RuleDefinition(BaseModel):
    """DB-backed rule registry entry — config (thresholds etc.) lives here,
    not in code, per spec's 'configurable without changing application code'."""
    __tablename__ = "rule_definitions"
    rule_key: Mapped[str] = mapped_column(String, unique=True, index=True)  # matches code-side rule class key
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, index=True)  # document|metadata|financial|invoice|receipt|contract|policy|fraud|compliance
    severity: Mapped[str] = mapped_column(String, default="medium")  # low|medium|high|critical
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    applicable_document_types: Mapped[list] = mapped_column(JSON, default=list)  # [] = all types
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # thresholds, allowlists, etc.
    effective_date: Mapped[str] = mapped_column(String, nullable=True)
    expiration_date: Mapped[str] = mapped_column(String, nullable=True)

class RuleFinding(BaseModel):
    __tablename__ = "rule_findings"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    rule_key: Mapped[str] = mapped_column(String, index=True)
    rule_version: Mapped[int] = mapped_column(Integer)
    rule_name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    triggered: Mapped[bool] = mapped_column(Boolean)
    description: Mapped[str] = mapped_column(String)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    recommendation: Mapped[str] = mapped_column(String, nullable=True)

class RuleExecutionRun(BaseModel):
    __tablename__ = "rule_execution_runs"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    rules_executed: Mapped[int] = mapped_column(default=0)
    rules_triggered: Mapped[int] = mapped_column(default=0)
    rules_failed: Mapped[int] = mapped_column(default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String, default="low")
    review_route: Mapped[str] = mapped_column(String, default="auto_approve")
    status: Mapped[str] = mapped_column(String, default="completed")

class RuleAuditLog(BaseModel):
    __tablename__ = "rule_audit_logs"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String)  # created|modified|enabled|disabled|executed|triggered|failed
    rule_key: Mapped[str] = mapped_column(String, nullable=True)
    detail: Mapped[str] = mapped_column(String, nullable=True)