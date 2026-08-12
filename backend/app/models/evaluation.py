# ===== app/models/evaluation.py =====
from sqlalchemy import String, Float, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class EvalDataset(BaseModel):
    __tablename__ = "eval_datasets"
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

class EvalCase(BaseModel):
    __tablename__ = "eval_cases"
    dataset_id: Mapped[str] = mapped_column(ForeignKey("eval_datasets.id"), index=True)
    query: Mapped[str] = mapped_column(String)
    expected_answer: Mapped[str] = mapped_column(String, nullable=True)
    relevant_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    relevant_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    relevant_pages: Mapped[dict] = mapped_column(JSON, default=dict)  # {document_id: [pages]}
    expected_citations: Mapped[list] = mapped_column(JSON, default=list)
    ground_truth_facts: Mapped[dict] = mapped_column(JSON, default=dict)
    document_type: Mapped[str] = mapped_column(String, nullable=True)
    difficulty: Mapped[str] = mapped_column(String, default="easy")  # easy|medium|hard|complex
    scenario: Mapped[str] = mapped_column(String, default="factual")
    metadata_filters: Mapped[dict] = mapped_column(JSON, default=dict)

class EvalRun(BaseModel):
    __tablename__ = "eval_runs"
    dataset_id: Mapped[str] = mapped_column(ForeignKey("eval_datasets.id"), index=True)
    dataset_version: Mapped[int] = mapped_column(Integer)
    config_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)  # embedding model, chunker, reranker, llm, rule version...
    case_count: Mapped[int] = mapped_column(default=0)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # aggregated metrics
    status: Mapped[str] = mapped_column(String, default="completed")
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)

class EvalCaseResult(BaseModel):
    __tablename__ = "eval_case_results"
    run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("eval_cases.id"), index=True)
    retrieved_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    reranked_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    generated_answer: Mapped[str] = mapped_column(String, nullable=True)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # per-case metric values
    latency_ms: Mapped[dict] = mapped_column(JSON, default=dict)  # per-stage latency
    passed: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_reason: Mapped[str] = mapped_column(String, nullable=True)

class QualityGate(BaseModel):
    __tablename__ = "quality_gates"
    metric_name: Mapped[str] = mapped_column(String, unique=True)  # e.g. "recall_at_10"
    min_value: Mapped[float] = mapped_column(Float, nullable=True)
    max_value: Mapped[float] = mapped_column(Float, nullable=True)
    environment: Mapped[str] = mapped_column(String, default="production")
