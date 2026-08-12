
# ===== app/rule_engine/history_lookup.py =====
"""Cross-document lookups needed by duplicate/fraud rules — kept separate
from single-document rule evaluation since it requires DB queries."""
from sqlalchemy import select
from app.models.knowledge import Entity, Fact

async def build_history_context(db, document_id: str, document_type: str, entities: list, facts: dict) -> dict:
    history = {}

    invoice_number_entity = next((e for e in entities if e.get("entity_type") == "invoice_number"), None)
    if invoice_number_entity:
        result = await db.execute(
            select(Entity.document_id).where(
                Entity.entity_type == "invoice_number", Entity.value == invoice_number_entity["value"],
                Entity.document_id != document_id,
            )
        )
        history["duplicate_invoice_numbers"] = [r[0] for r in result.all()]

    vendor = None  # populated by caller from metadata if available
    history["near_threshold_invoices_same_vendor"] = []  # left as extension point —
    # requires vendor + amount range query; not fabricated without real vendor-normalization logic

    return history