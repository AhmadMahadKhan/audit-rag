# ===== app/repositories/monitoring_repository.py =====
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.models.monitoring import ErrorEvent, LLMUsageEvent, AlertRule, AlertEvent

class MonitoringRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_top_errors(self, limit: int = 20) -> list[ErrorEvent]:
        result = await self.db.execute(select(ErrorEvent).order_by(desc(ErrorEvent.occurrence_count)).limit(limit))
        return result.scalars().all()

    async def get_errors_by_category(self) -> dict:
        result = await self.db.execute(select(ErrorEvent.category, func.sum(ErrorEvent.occurrence_count)).group_by(ErrorEvent.category))
        return dict(result.all())

    async def log_llm_usage(self, event: LLMUsageEvent):
        self.db.add(event)
        await self.db.commit()

    async def get_llm_cost_summary(self, hours: int = 24) -> dict:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(LLMUsageEvent.model, func.sum(LLMUsageEvent.estimated_cost), func.sum(LLMUsageEvent.input_tokens),
                   func.sum(LLMUsageEvent.output_tokens), func.count(LLMUsageEvent.id))
            .where(LLMUsageEvent.created_at >= since).group_by(LLMUsageEvent.model)
        )
        return {row[0]: {"cost": row[1], "input_tokens": row[2], "output_tokens": row[3], "requests": row[4]}
                for row in result.all()}

    async def get_cost_by_user(self, hours: int = 24, limit: int = 20) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(LLMUsageEvent.user_id, func.sum(LLMUsageEvent.estimated_cost))
            .where(LLMUsageEvent.created_at >= since, LLMUsageEvent.user_id.isnot(None))
            .group_by(LLMUsageEvent.user_id).order_by(desc(func.sum(LLMUsageEvent.estimated_cost))).limit(limit)
        )
        return [{"user_id": r[0], "cost": r[1]} for r in result.all()]

    async def get_active_alert_rules(self) -> list[AlertRule]:
        result = await self.db.execute(select(AlertRule).where(AlertRule.is_active == True))
        return result.scalars().all()

    async def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        self.db.add(rule); await self.db.commit(); await self.db.refresh(rule)
        return rule

    async def fire_alert(self, event: AlertEvent) -> AlertEvent:
        self.db.add(event); await self.db.commit(); await self.db.refresh(event)
        return event

    async def get_active_alerts(self) -> list[AlertEvent]:
        result = await self.db.execute(select(AlertEvent).where(AlertEvent.status == "firing"))
        return result.scalars().all()

    async def acknowledge_alert(self, alert_id: str, user_id: str):
        result = await self.db.execute(select(AlertEvent).where(AlertEvent.id == alert_id))
        alert = result.scalar_one_or_none()
        if alert:
            alert.status = "acknowledged"
            alert.acknowledged_by = user_id
            await self.db.commit()