
# ===== app/services/extraction_service.py =====
from app.canonical.schema import CanonicalDocument
from app.extraction.entity_extractors import RegexEntityExtractor
from app.extraction.ai_entity_extractor import AIEntityExtractor
from app.extraction.date_number_extractors import DateEntityExtractor
from app.extraction.fact_extractor import FinancialFactExtractor
from app.extraction.line_item_extractor import LineItemExtractor
from app.extraction.validator import validate_facts, validate_line_item
from app.models.knowledge import Entity, Fact, LineItem, KnowledgeRelationship, ExtractionRun
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.canonical_repository import CanonicalRepository
from app.repositories.document_repository import DocumentRepository
from app.services.activity_logger import log_activity
from app.core.exceptions import DocumentNotFound, ValidationFailed
from app.core.config import settings
from app.core.logging_config import logger

class ExtractionService:
    def __init__(self, db):
        self.db = db
        self.repo = KnowledgeRepository(db)
        self.canonical_repo = CanonicalRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def extract_all(self, document_id: str, use_ai: bool = False) -> ExtractionRun:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound(f"Document {document_id} not found")

        canonical_record = await self.canonical_repo.get_latest(document_id)
        if not canonical_record:
            raise ValidationFailed("No canonical document available")
        doc = CanonicalDocument(**canonical_record.canonical_json)

        # --- Entities ---
        raw_entities = RegexEntityExtractor().extract(doc) + DateEntityExtractor().extract(doc)
        if use_ai:
            raw_entities += await AIEntityExtractor().extract(doc)

        entity_rows = [Entity(document_id=document_id, entity_type=e.entity_type, value=e.value,
                               canonical_value=e.canonical_value, confidence=e.confidence, page=e.page,
                               block_id=e.block_id, bbox=e.bbox, method=e.method, extractor_version="1.0")
                        for e in raw_entities]

        # --- Facts ---
        raw_facts = FinancialFactExtractor().extract(doc)
        fact_numeric = {f.fact_type: f.numeric_value for f in raw_facts if f.numeric_value is not None}
        issues = dict(validate_facts(fact_numeric))

        fact_rows = [Fact(document_id=document_id, fact_type=f.fact_type, value=f.value,
                           numeric_value=f.numeric_value, confidence=f.confidence,
                           status="needs_review" if f.fact_type in issues else "valid",
                           validation_note=issues.get(f.fact_type)) for f in raw_facts]

        # --- Line items ---
        raw_items = LineItemExtractor().extract(doc)
        item_rows = []
        invalid_items = 0
        for i in raw_items:
            note = validate_line_item(i)
            if note:
                invalid_items += 1
            item_rows.append(LineItem(document_id=document_id, table_id=i.table_id, row_index=i.row_index,
                                        item_name=i.item_name, description=i.description, quantity=i.quantity,
                                        unit_price=i.unit_price, tax=i.tax, discount=i.discount,
                                        line_total=i.line_total, validation_status="needs_review" if note else "valid"))

        # --- Relationships (simple heuristics) ---
        relationship_rows = []
        vendor_entities = [e for e in entity_rows if e.entity_type in ("vendor", "organization")]
        invoice_entities = [e for e in entity_rows if e.entity_type == "invoice_number"]
        if vendor_entities and invoice_entities:
            relationship_rows.append(KnowledgeRelationship(
                document_id=document_id, relationship_type="vendor_invoice", source_type="entity",
                source_id=vendor_entities[0].id if vendor_entities[0].id else "pending",
                target_type="entity", target_id="pending", confidence=0.5,
            ))
        # Note: since ids aren't assigned until insert, this simple relation is best-effort;
        # full graph relationships should be built post-insert in a follow-up pass if needed.

        await self.repo.replace_all(document_id, entity_rows, fact_rows, item_rows, [])

        run = await self.repo.create_run(ExtractionRun(
            document_id=document_id, entity_count=len(entity_rows), fact_count=len(fact_rows),
            line_item_count=len(item_rows), invalid_fact_count=len(issues) + invalid_items,
            status="completed" if not issues and not invalid_items else "needs_review",
        ))

        document.processing_status = "extracted"
        await self.db.commit()

        logger.info("extraction_completed", document_id=document_id, entities=len(entity_rows),
                     facts=len(fact_rows), line_items=len(item_rows))
        await log_activity(self.db, "entities_extracted", user_id=document.user_id, related_document_id=document_id)
        return run
