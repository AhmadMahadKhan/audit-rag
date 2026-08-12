
# ===== app/repositories/evaluation_repository.py =====
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evaluation import EvalDataset, EvalCase, EvalRun, EvalCaseResult, QualityGate

class EvaluationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dataset(self, ds: EvalDataset) -> EvalDataset:
        self.db.add(ds); await self.db.commit(); await self.db.refresh(ds)
        return ds

    async def get_dataset(self, dataset_id: str) -> EvalDataset | None:
        result = await self.db.execute(select(EvalDataset).where(EvalDataset.id == dataset_id))
        return result.scalar_one_or_none()

    async def add_case(self, case: EvalCase) -> EvalCase:
        self.db.add(case); await self.db.commit(); await self.db.refresh(case)
        return case

    async def get_cases(self, dataset_id: str) -> list[EvalCase]:
        result = await self.db.execute(select(EvalCase).where(EvalCase.dataset_id == dataset_id))
        return result.scalars().all()

    async def create_run(self, run: EvalRun) -> EvalRun:
        self.db.add(run); await self.db.commit(); await self.db.refresh(run)
        return run

    async def save_case_result(self, result: EvalCaseResult):
        self.db.add(result); await self.db.commit()

    async def get_run(self, run_id: str) -> EvalRun | None:
        result = await self.db.execute(select(EvalRun).where(EvalRun.id == run_id))
        return result.scalar_one_or_none()

    async def get_run_case_results(self, run_id: str) -> list[EvalCaseResult]:
        result = await self.db.execute(select(EvalCaseResult).where(EvalCaseResult.run_id == run_id))
        return result.scalars().all()

    async def get_baseline(self, dataset_id: str) -> EvalRun | None:
        result = await self.db.execute(
            select(EvalRun).where(EvalRun.dataset_id == dataset_id, EvalRun.is_baseline == True)
        )
        return result.scalar_one_or_none()

    async def get_gates(self, environment: str = "production") -> list[QualityGate]:
        result = await self.db.execute(select(QualityGate).where(QualityGate.environment == environment))
        return result.scalars().all()

    async def upsert_gate(self, gate: QualityGate):
        self.db.add(gate); await self.db.commit()