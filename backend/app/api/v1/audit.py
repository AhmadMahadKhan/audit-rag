
# ===== app/api/v1/audit.py =====
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.audit_agent_service import AuditAgentService, execute_audit_run
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_agent import StartAuditRequest, AuditRunOut, AuditSnapshotOut, AuditReportOut
from app.core.exceptions import DocumentNotFound
from fastapi.responses import Response
from app.services.pdf_export import render_audit_report_pdf

router = APIRouter(prefix="/audit", tags=["audit-agent"])

@router.post("/runs", response_model=AuditRunOut)
async def start_audit(payload: StartAuditRequest, background_tasks: BackgroundTasks,
                        db: AsyncSession = Depends(get_db), user=Depends(require_permission("analytics.read"))):
    service = AuditAgentService(db)
    document_ids = await service.resolve_document_ids(payload.document_ids, user)
    run = await service.start_run(payload.name, document_ids, user.id)
    background_tasks.add_task(execute_audit_run, run.id)
    return run

@router.get("/runs", response_model=list[AuditRunOut])
async def list_runs(db: AsyncSession = Depends(get_db), user=Depends(require_permission("analytics.read"))):
    return await AuditRepository(db).list_runs(user.id)

@router.get("/runs/{run_id}", response_model=AuditRunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("analytics.read"))):
    run = await AuditRepository(db).get_run(run_id)
    if not run:
        raise DocumentNotFound("Audit run not found")
    return run

@router.get("/runs/{run_id}/memory", response_model=list[AuditSnapshotOut])
async def get_memory_trail(run_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("analytics.read"))):
    """Inspect the running memory after each document — useful for
    understanding how the auditor's picture evolved, not just the end result."""
    return await AuditRepository(db).get_snapshots(run_id)

@router.get("/runs/{run_id}/report", response_model=AuditReportOut)
async def get_report(run_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("analytics.read"))):
    report = await AuditRepository(db).get_report(run_id)
    if not report:
        raise DocumentNotFound("Report not ready yet — check run status first")
    return report

@router.get("/runs/{run_id}/report/pdf")
async def get_report_pdf(run_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("analytics.read"))):
    report = await AuditRepository(db).get_report(run_id)
    if not report:
        raise DocumentNotFound("Report not ready yet — check run status first")

    run = await AuditRepository(db).get_run(run_id)
    run_name = run.name if run else "Audit Report"

    pdf_bytes = render_audit_report_pdf(run_name, report.content_markdown, report.created_at)

    filename = f"audit_report_{run_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )