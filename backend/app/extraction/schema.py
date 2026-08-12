# ===== app/extraction/schema.py =====
from pydantic import BaseModel

class ExtractedEntity(BaseModel):
    entity_type: str
    value: str
    canonical_value: str | None = None
    confidence: float
    page: int | None = None
    block_id: str | None = None
    bbox: dict | None = None
    method: str = "rule_based"

class ExtractedFact(BaseModel):
    fact_type: str
    value: str
    numeric_value: float | None = None
    confidence: float
    source_entity_index: int | None = None  # index into entities list, resolved later

class ExtractedLineItem(BaseModel):
    table_id: str | None
    row_index: int
    item_name: str | None = None
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    tax: float | None = None
    discount: float | None = None
    line_total: float | None = None