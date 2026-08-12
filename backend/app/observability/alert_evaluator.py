# ===== app/observability/alert_evaluator.py =====
"""Evaluates active alert rules against current Prometheus metric snapshots.
Meant to run on a schedule (cron/Celery beat) — see note in service."""
from app.observability.metrics import (
    API_REQUEST_LATENCY, LLM_REQUESTS, OCR_REQUESTS,
)
from app.models.monitoring import AlertEvent
from app.repositories.monitoring_repository import MonitoringRepository
from app.core.logging_config import logger

def check_condition(value: float, condition: str, threshold: float) -> bool:
    if condition == "gt":
        return value > threshold
    if condition == "lt":
        return value < threshold
    if condition == "eq":
        return value == threshold
    return False

class AlertEvaluator:
    """Metric values passed in explicitly (from a scrape or aggregation job) —
    this class doesn't scrape Prometheus itself, keeping it testable and
    decoupled from the metrics backend."""
    def __init__(self, db):
        self.db = db
        self.repo = MonitoringRepository(db)

    async def evaluate(self, current_metrics: dict[str, float]) -> list[AlertEvent]:
        rules = await self.repo.get_active_alert_rules()
        fired = []
        for rule in rules:
            value = current_metrics.get(rule.metric_name)
            if value is None:
                continue
            if check_condition(value, rule.condition, rule.threshold):
                event = await self.repo.fire_alert(AlertEvent(
                    rule_id=rule.id, rule_name=rule.name, severity=rule.severity,
                    metric_value=value, threshold=rule.threshold,
                ))
                fired.append(event)
                logger.warning("alert_fired", rule=rule.name, value=value, threshold=rule.threshold, severity=rule.severity)
        return fired