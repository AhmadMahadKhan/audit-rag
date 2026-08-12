
# ===== app/api/v1/monitoring.py =====
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.repositories.monitoring_repository import MonitoringRepository
from app.observability.alert_evaluator import AlertEvaluator
from app.models.monitoring import AlertRule

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/metrics")
async def prometheus_metrics():
    """Scrape endpoint — no auth per Prometheus convention; secure at network/ingress level."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/errors/top")
async def top_errors(db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await MonitoringRepository(db).get_top_errors()

@router.get("/errors/by-category")
async def errors_by_category(db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await MonitoringRepository(db).get_errors_by_category()

@router.get("/costs/summary")
async def cost_summary(hours: int = 24, db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await MonitoringRepository(db).get_llm_cost_summary(hours)

@router.get("/costs/by-user")
async def cost_by_user(hours: int = 24, db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await MonitoringRepository(db).get_cost_by_user(hours)

@router.post("/alerts/rules")
async def create_alert_rule(name: str, metric_name: str, condition: str, threshold: float, severity: str,
                              db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    rule = AlertRule(name=name, metric_name=metric_name, condition=condition, threshold=threshold, severity=severity)
    return await MonitoringRepository(db).create_alert_rule(rule)

@router.get("/alerts/active")
async def active_alerts(db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    return await MonitoringRepository(db).get_active_alerts()

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge(alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("settings.manage"))):
    await MonitoringRepository(db).acknowledge_alert(alert_id, user.id)
    return {"success": True}

@router.post("/alerts/evaluate")
async def evaluate_alerts(current_metrics: dict[str, float], db: AsyncSession = Depends(get_db), _=Depends(require_permission("settings.manage"))):
    """Manual/cron-triggered evaluation — pass current metric snapshot (e.g. from a
    scheduled job that queries Prometheus)."""
    fired = await AlertEvaluator(db).evaluate(current_metrics)
    return {"fired": len(fired)}