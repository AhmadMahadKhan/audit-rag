
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

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/datasets", response_model=list[EvalDatasetOut])
async def list_datasets(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await EvaluationRepository(db).list_datasets()

@router.post("/datasets", response_model=EvalDatasetOut)
async def create_dataset(name: str, description: str | None = None, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await EvaluationRepository(db).create_dataset(EvalDataset(name=name, description=description))

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