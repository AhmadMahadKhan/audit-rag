# ===== app/api/v1/dashboard.py =====
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.dependencies.auth import require_permission
from app.schemas.dashboard import DashboardSummary, ActivityItem, SystemHealth, ChartSeries

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummary)
async def summary(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await DashboardService(db).get_summary()

@router.get("/activity", response_model=list[ActivityItem])
async def activity(limit: int = Query(20, le=100), db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await DashboardService(db).get_recent_activity(limit)

@router.get("/health", response_model=SystemHealth)
async def health(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await DashboardService(db).get_system_health()

@router.get("/charts/upload-trend", response_model=ChartSeries)
async def upload_trend(days: int = Query(14, le=90), db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await DashboardService(db).get_upload_trend(days)

@router.get("/charts/document-types", response_model=ChartSeries)
async def document_types(db: AsyncSession = Depends(get_db), _=Depends(require_permission("analytics.read"))):
    return await DashboardService(db).get_document_type_distribution()
