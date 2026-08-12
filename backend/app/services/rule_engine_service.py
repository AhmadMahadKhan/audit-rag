# ===== app/services/rule_engine_service.py =====
from app.rule_engine.base import RuleContext
from app.rule_engine.executor import execute_rules
from app.rule_engine.risk_scoring import calculate_risk_score, score_to_level, route_for_level
from app.rule_engine.history_lookup import build_history_context
from app.rule_engine.registry import get_rule_class, ALL_RULES
from app.models.rule_engine import RuleDefinition, RuleFinding, RuleExecutionRun, RuleAuditLog
from app.repositories.rule_repository import RuleRepository
from app.repositories.canonical_repository import CanonicalRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.config import settings
from app.core.exceptions import DocumentNotFound, RuleEngineError
from app.core.logging_config import logger

class RuleEngineService:
    def __init__(self, db):
        self.db = db
        self.repo = RuleRepository(db)
        self.canonical_repo = CanonicalRepository(db)
        self.metadata_repo = MetadataRepository(db)
        self.knowledge_repo = KnowledgeRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def seed_default_rules(self):
        """Idempotent — call once at startup or via admin endpoint to populate
        RuleDefinition rows from the code-side registry."""
        existing = {d.rule_key for d in await self.repo.get_all_definitions()}
        for cls in ALL_RULES:
            if cls.key not in existing:
                await self.repo.create(RuleDefinition(
                    rule_key=cls.key, name=cls.name, description=cls.name, category=cls.category,
                    severity=cls.default_severity, is_active=True,
                    applicable_document_types=cls.applicable_document_types, config={},
                ))

    async def evaluate_document(self, document_id: str, user_id: str | None = None) -> RuleExecutionRun:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        canonical_record = await self.canonical_repo.get_latest(document_id)
        metadata_fields = await self.metadata_repo.get_for_document(document_id)
        entities = await self.knowledge_repo.get_entities(document_id)
        facts_rows = await self.knowledge_repo.get_facts(document_id)
        line_items = await self.knowledge_repo.get_line_items(document_id)

        metadata_dict = {f.key: f.value for f in metadata_fields}
        facts_dict = {f.fact_type: f.numeric_value for f in facts_rows if f.numeric_value is not None}
        entities_list = [{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence,
                          "page": e.page, "block_id": e.block_id} for e in entities]
        line_items_list = [{"item_name": li.item_name, "quantity": li.quantity, "unit_price": li.unit_price,
                            "line_total": li.line_total} for li in line_items]

        history = await build_history_context(self.db, document_id, document.document_type, entities_list, facts_dict)

        definitions = await self.repo.get_active_definitions()
        active_keys = {d.rule_key for d in definitions}
        rule_configs = {d.rule_key: d.config for d in definitions}
        version_map = {d.rule_key: d.version for d in definitions}

        ctx = RuleContext(
            document_id=document_id, document_type=document.document_type or "unknown",
            canonical=canonical_record.canonical_json if canonical_record else None,
            metadata=metadata_dict, entities=entities_list, facts=facts_dict, facts_raw=facts_rows,
            line_items=line_items_list, raw_text=canonical_record.canonical_json.get("raw_text", "") if canonical_record else "",
            history=history,
        )

        results, failed_keys = await execute_rules(ctx, active_keys, rule_configs)

        finding_rows = []
        for r in results:
            finding_rows.append(RuleFinding(
                document_id=document_id, rule_key=r.rule_key, rule_version=version_map.get(r.rule_key, 1),
                rule_name=get_rule_class(r.rule_key).name, category=get_rule_class(r.rule_key).category,
                severity=r.severity, triggered=r.triggered, description=r.description,
                evidence=r.evidence, confidence=r.confidence, recommendation=r.recommendation,
            ))
        await self.repo.save_findings(finding_rows)

        findings_dicts = [{"triggered": r.triggered, "severity": r.severity, "confidence": r.confidence} for r in results]
        risk_score = calculate_risk_score(findings_dicts)
        thresholds = {"medium": settings.RISK_THRESHOLD_MEDIUM, "high": settings.RISK_THRESHOLD_HIGH,
                      "critical": settings.RISK_THRESHOLD_CRITICAL}
        risk_level = score_to_level(risk_score, thresholds)
        review_route = route_for_level(risk_level)

        run = await self.repo.create_run(RuleExecutionRun(
            document_id=document_id, rules_executed=len(results) + len(failed_keys),
            rules_triggered=sum(1 for r in results if r.triggered), rules_failed=len(failed_keys),
            risk_score=risk_score, risk_level=risk_level, review_route=review_route,
            status="completed" if not failed_keys else "partial_failure",
        ))

        document.processing_status = "rules_evaluated"
        await self.db.commit()

        await self.repo.audit(RuleAuditLog(user_id=user_id, action="executed",
                                             detail=f"document={document_id}, risk={risk_level}, triggered={run.rules_triggered}"))
        logger.info("rule_evaluation_completed", document_id=document_id, risk_score=risk_score,
                     risk_level=risk_level, triggered=run.rules_triggered, failed=len(failed_keys))
        await log_activity(self.db, "rule_engine_executed", user_id=document.user_id,
                            related_document_id=document_id, status=risk_level)
        return run

    async def set_rule_active(self, rule_key: str, is_active: bool, user_id: str):
        definition = await self.repo.get_by_key(rule_key)
        if not definition:
            raise RuleEngineError(f"Rule {rule_key} not found")
        definition.is_active = is_active
        await self.db.commit()
        await self.repo.audit(RuleAuditLog(user_id=user_id, action="enabled" if is_active else "disabled", rule_key=rule_key))

    async def update_rule_config(self, rule_key: str, config: dict, user_id: str):
        definition = await self.repo.get_by_key(rule_key)
        if not definition:
            raise RuleEngineError(f"Rule {rule_key} not found")
        definition.config = config
        definition.version += 1
        await self.db.commit()
        await self.repo.audit(RuleAuditLog(user_id=user_id, action="modified", rule_key=rule_key, detail=str(config)))
