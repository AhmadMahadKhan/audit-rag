
# ===== app/api/v1/evaluation.py =====
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.evaluation_service import EvaluationService
from app.repositories.evaluation_repository import EvaluationRepository
from app.models.evaluation import EvalDataset, EvalCase, QualityGate
from app.schemas.evaluation import (
    EvalDatasetOut, EvalCaseCreate, EvalRunOut, RunEvaluationRequest, QualityGateIn,
)
import json
import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.evaluation_service import EvaluationService
from app.repositories.evaluation_repository import EvaluationRepository
from app.models.evaluation import EvalDataset, EvalCase, QualityGate
from app.schemas.evaluation import (
    EvalDatasetOut, EvalCaseCreate, EvalRunOut, RunEvaluationRequest, QualityGateIn,
    CreateDatasetRequest, BulkCaseImportRequest, BulkImportResult,
)
from app.core.exceptions import ValidationFailed

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/datasets", response_model=list[EvalDatasetOut])
async def list_datasets(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).list_datasets()


@router.get("/datasets/{dataset_id}/cases")
async def get_dataset_cases(dataset_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).get_cases(dataset_id)

@router.get("/datasets/{dataset_id}/documents")
async def get_dataset_documents(dataset_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).get_dataset_documents(dataset_id)

@router.post("/datasets/{dataset_id}/cases")
async def add_case(dataset_id: str, payload: EvalCaseCreate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    case = EvalCase(dataset_id=dataset_id, **payload.model_dump())
    return await EvaluationRepository(db).add_case(case)

@router.post("/datasets/{dataset_id}/upload-documents")
async def upload_documents_to_dataset(
    dataset_id: str,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("settings.manage")),
):
    payload = [(f.filename, await f.read()) for f in files]
    return await EvaluationService(db).upload_and_generate_cases(dataset_id, payload, user.id)

@router.post("/datasets/{dataset_id}/run", response_model=EvalRunOut)
async def run_evaluation(dataset_id: str, payload: RunEvaluationRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await EvaluationService(db).run_evaluation(dataset_id, payload.config_snapshot, payload.generate_answers)

@router.get("/runs", response_model=list[EvalRunOut])
async def list_runs(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).list_runs()

@router.get("/runs/{run_id}", response_model=EvalRunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).get_run(run_id)

@router.get("/runs/{run_id}/failed-cases")
async def failed_cases(run_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    results = await EvaluationRepository(db).get_run_case_results(run_id)
    return [r for r in results if not r.passed]

@router.get("/runs/{run_id}/case-results")
async def get_run_case_results(run_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).get_run_case_results(run_id)

@router.get("/compare")
async def compare(run_a: str, run_b: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationService(db).compare_runs(run_a, run_b)

@router.get("/runs/{run_id}/regression-check")
async def regression_check(run_id: str, environment: str = "production", db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await EvaluationService(db).check_regression(run_id, environment)

@router.post("/gates")
async def set_gate(payload: QualityGateIn, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    await EvaluationRepository(db).upsert_gate(QualityGate(**payload.model_dump()))
    return {"success": True}

from app.core.exceptions import ValidationFailed



@router.post("/datasets", response_model=EvalDatasetOut)
async def create_dataset(payload: CreateDatasetRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await EvaluationRepository(db).create_dataset(EvalDataset(name=payload.name, description=payload.description))

@router.get("/datasets", response_model=list[EvalDatasetOut])
async def list_datasets(db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await EvaluationRepository(db).list_datasets()

@router.post("/datasets/{dataset_id}/cases", response_model=EvalCaseCreate)
async def add_case(dataset_id: str, payload: EvalCaseCreate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    case = EvalCase(dataset_id=dataset_id, **payload.model_dump())
    return await EvaluationRepository(db).add_case(case)

@router.post("/datasets/{dataset_id}/cases/bulk", response_model=BulkImportResult)
async def bulk_add_cases(dataset_id: str, payload: BulkCaseImportRequest, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    """Paste a JSON array of cases directly in Swagger's request body — no repeated one-by-one calls."""
    repo = EvaluationRepository(db)
    imported, errors = 0, []
    for i, case_data in enumerate(payload.cases):
        try:
            case = EvalCase(dataset_id=dataset_id, **case_data.model_dump())
            await repo.add_case(case)
            imported += 1
        except Exception as e:
            errors.append(f"case[{i}]: {str(e)}")
    return BulkImportResult(dataset_id=dataset_id, imported=imported, failed=len(errors), errors=errors)

@router.post("/datasets/{dataset_id}/cases/import-file", response_model=BulkImportResult)
async def import_cases_file(dataset_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    """Upload a .json (array of case objects) or .csv file — the actual file-picker workflow."""
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".json"):
        try:
            raw_cases = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValidationFailed(f"Invalid JSON: {e}")
        if not isinstance(raw_cases, list):
            raise ValidationFailed("JSON file must contain a top-level array of case objects")

    elif filename.endswith(".csv"):
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        raw_cases = []
        for row in reader:
            # JSON-ish columns (ground_truth_facts, relevant_document_ids, etc.) are
            # stored as JSON strings in CSV cells — parse them back, default to empty
            case = {
                "query": row.get("query", ""),
                "expected_answer": row.get("expected_answer") or None,
                "document_type": row.get("document_type") or None,
                "difficulty": row.get("difficulty") or "easy",
                "scenario": row.get("scenario") or "factual",
            }
            for json_field in ("relevant_document_ids", "relevant_chunk_ids", "expected_citations", "ground_truth_facts", "metadata_filters"):
                raw_val = row.get(json_field, "")
                try:
                    case[json_field] = json.loads(raw_val) if raw_val else ({} if "facts" in json_field or "filters" in json_field else [])
                except json.JSONDecodeError:
                    case[json_field] = {} if "facts" in json_field or "filters" in json_field else []
            raw_cases.append(case)
    else:
        raise ValidationFailed("Only .json or .csv files are supported")

    repo = EvaluationRepository(db)
    imported, errors = 0, []
    for i, raw in enumerate(raw_cases):
        try:
            validated = EvalCaseCreate(**raw)
            case = EvalCase(dataset_id=dataset_id, **validated.model_dump())
            await repo.add_case(case)
            imported += 1
        except Exception as e:
            errors.append(f"row[{i}]: {str(e)}")

    return BulkImportResult(dataset_id=dataset_id, imported=imported, failed=len(errors), errors=errors)
