
# ===== app/repositories/audit_repository.py =====
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_agent import AuditRun, AuditMemorySnapshot, AuditReport

class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_run(self, run: AuditRun) -> AuditRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_run(self, run_id: str) -> AuditRun | None:
        result = await self.db.execute(select(AuditRun).where(AuditRun.id == run_id))
        return result.scalar_one_or_none()

    async def list_runs(self, user_id: str) -> list[AuditRun]:
        result = await self.db.execute(select(AuditRun).where(AuditRun.requested_by == user_id).order_by(AuditRun.created_at.desc()))
        return result.scalars().all()

    async def update_progress(self, run: AuditRun, current: int, stage: str):
        run.progress_current = current
        run.current_stage = stage
        await self.db.commit()

    async def save_snapshot(self, snapshot: AuditMemorySnapshot):
        self.db.add(snapshot)
        await self.db.commit()

    async def get_snapshots(self, run_id: str) -> list[AuditMemorySnapshot]:
        result = await self.db.execute(
            select(AuditMemorySnapshot).where(AuditMemorySnapshot.run_id == run_id).order_by(AuditMemorySnapshot.order_index)
        )
        return result.scalars().all()

    async def save_report(self, report: AuditReport) -> AuditReport:
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_report(self, run_id: str) -> AuditReport | None:
        result = await self.db.execute(select(AuditReport).where(AuditReport.run_id == run_id))
        return result.scalar_one_or_none()

    async def get_latest_rule_run(self, document_id: str):
        from app.models.rule_engine import RuleExecutionRun
        result = await self.db.execute(
            select(RuleExecutionRun).where(RuleExecutionRun.document_id == document_id)
            .order_by(RuleExecutionRun.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
