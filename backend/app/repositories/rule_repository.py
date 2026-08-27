from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rule_engine import RuleDefinition, RuleFinding, RuleExecutionRun, RuleAuditLog

class RuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_definitions(self) -> list[RuleDefinition]:
        result = await self.db.execute(select(RuleDefinition))
        return result.scalars().all()

    async def get_active_definitions(self) -> list[RuleDefinition]:
        result = await self.db.execute(select(RuleDefinition).where(RuleDefinition.is_active == True))
        return result.scalars().all()

    async def get_by_key(self, rule_key: str) -> RuleDefinition | None:
        result = await self.db.execute(select(RuleDefinition).where(RuleDefinition.rule_key == rule_key))
        return result.scalar_one_or_none()

    async def create(self, definition: RuleDefinition) -> RuleDefinition:
        self.db.add(definition)
        await self.db.commit()
        await self.db.refresh(definition)
        return definition

    async def save_findings(self, findings: list[RuleFinding]):
        if findings:
            doc_id = findings[0].document_id
            await self.db.execute(delete(RuleFinding).where(RuleFinding.document_id == doc_id))
        for f in findings:
            self.db.add(f)
        await self.db.commit()

    async def get_findings(self, document_id: str) -> list[RuleFinding]:
        result = await self.db.execute(select(RuleFinding).where(RuleFinding.document_id == document_id))
        return result.scalars().all()

    async def create_run(self, run: RuleExecutionRun) -> RuleExecutionRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def audit(self, log: RuleAuditLog):
        self.db.add(log)
        await self.db.commit()