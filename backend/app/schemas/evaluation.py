
# # ===== app/schemas/evaluation.py =====
from pydantic import BaseModel
from datetime import datetime



class EvalCaseCreate(BaseModel):
    query: str
    expected_answer: str | None = None
    relevant_document_ids: list[str] = []
    relevant_chunk_ids: list[str] = []
    expected_citations: list[dict] = []
    ground_truth_facts: dict = {}
    document_type: str | None = None
    difficulty: str = "easy"
    scenario: str = "factual"
    metadata_filters: dict = {}

class EvalRunOut(BaseModel):
    id: str
    dataset_id: str
    case_count: int
    metrics: dict
    status: str
    is_baseline: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RunEvaluationRequest(BaseModel):
    config_snapshot: dict = {}
    generate_answers: bool = True

class QualityGateIn(BaseModel):
    metric_name: str
    min_value: float | None = None
    max_value: float | None = None
    environment: str = "production"

# ===== app/schemas/evaluation.py (ADD/FIX) =====

class CreateDatasetRequest(BaseModel):
    name: str
    description: str | None = None

class EvalDatasetOut(BaseModel):
    id: str
    name: str
    description: str | None
    version: int

    class Config:
        from_attributes = True

class EvalCaseCreate(BaseModel):
    query: str
    expected_answer: str | None = None
    relevant_document_ids: list[str] = []
    relevant_chunk_ids: list[str] = []
    expected_citations: list[dict] = []
    ground_truth_facts: dict = {}
    document_type: str | None = None
    difficulty: str = "easy"
    scenario: str = "factual"
    metadata_filters: dict = {}

class BulkCaseImportRequest(BaseModel):
    cases: list[EvalCaseCreate]

class BulkImportResult(BaseModel):
    dataset_id: str
    imported: int
    failed: int
    errors: list[str] = []