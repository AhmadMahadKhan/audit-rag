
# ===== app/repositories/knowledge_repository.py =====
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import Entity, Fact, LineItem, KnowledgeRelationship, ExtractionRun

class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def replace_all(self, document_id: str, entities, facts, line_items, relationships):
        for model in (Entity, Fact, LineItem, KnowledgeRelationship):
            await self.db.execute(delete(model).where(model.document_id == document_id))
        for obj in [*entities, *facts, *line_items, *relationships]:
            self.db.add(obj)
        await self.db.commit()

    async def get_entities(self, document_id: str) -> list[Entity]:
        result = await self.db.execute(select(Entity).where(Entity.document_id == document_id))
        return result.scalars().all()

    async def get_facts(self, document_id: str) -> list[Fact]:
        result = await self.db.execute(select(Fact).where(Fact.document_id == document_id))
        return result.scalars().all()

    async def get_line_items(self, document_id: str) -> list[LineItem]:
        result = await self.db.execute(select(LineItem).where(LineItem.document_id == document_id))
        return result.scalars().all()

    async def get_relationships(self, document_id: str) -> list[KnowledgeRelationship]:
        result = await self.db.execute(select(KnowledgeRelationship).where(KnowledgeRelationship.document_id == document_id))
        return result.scalars().all()

    async def search_entities(self, entity_type: str | None, value_contains: str | None, skip=0, limit=50):
        query = select(Entity)
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        if value_contains:
            query = query.where(Entity.value.ilike(f"%{value_contains}%"))
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def search_facts(self, fact_type: str | None, skip=0, limit=50):
        query = select(Fact)
        if fact_type:
            query = query.where(Fact.fact_type == fact_type)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create_run(self, run: ExtractionRun) -> ExtractionRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run
