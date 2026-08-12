# ===== app/api/v1/rule_engine.py =====
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.services.rule_engine_service import RuleEngineService
from app.repositories.rule_repository import RuleRepository
from app.schemas.rule_engine import RuleDefinitionOut, RuleConfigUpdate, RuleFindingOut, RuleExecutionRunOut

router = APIRouter(prefix="/rules", tags=["rule-engine"])

@router.get("", response_model=list[RuleDefinitionOut])
async def list_rules(db: AsyncSession = Depends(get_db), _=Depends(require_permission("rules.manage"))):
    return await RuleRepository(db).get_all_definitions()

@router.post("/seed")
async def seed_rules(db: AsyncSession = Depends(get_db), _=Depends(require_permission("rules.manage"))):
    await RuleEngineService(db).seed_default_rules()
    return {"success": True}

@router.post("/{rule_key}/enable")
async def enable_rule(rule_key: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("rules.manage"))):
    await RuleEngineService(db).set_rule_active(rule_key, True, user.id)
    return {"success": True}

@router.post("/{rule_key}/disable")
async def disable_rule(rule_key: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("rules.manage"))):
    await RuleEngineService(db).set_rule_active(rule_key, False, user.id)
    return {"success": True}

@router.put("/{rule_key}/config")
async def update_config(rule_key: str, payload: RuleConfigUpdate, db: AsyncSession = Depends(get_db), user=Depends(require_permission("rules.manage"))):
    await RuleEngineService(db).update_rule_config(rule_key, payload.config, user.id)
    return {"success": True}

@router.post("/{document_id}/execute", response_model=RuleExecutionRunOut)
async def execute_rules_for_document(document_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_permission("documents.upload"))):
    return await RuleEngineService(db).evaluate_document(document_id, user.id)

@router.get("/{document_id}/findings", response_model=list[RuleFindingOut])
async def get_findings(document_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_permission("documents.read"))):
    return await RuleRepository(db).get_findings(document_id)