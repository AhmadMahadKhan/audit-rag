
# ===== app/schemas/knowledge.py =====
from pydantic import BaseModel
from datetime import datetime

class EntityOut(BaseModel):
    id: str
    entity_type: str
    value: str
    confidence: float
    page: int | None
    method: str

    class Config:
        from_attributes = True

class FactOut(BaseModel):
    id: str
    fact_type: str
    value: str
    numeric_value: float | None
    confidence: float
    status: str
    validation_note: str | None

    class Config:
        from_attributes = True

class LineItemOut(BaseModel):
    id: str
    item_name: str | None
    quantity: float | None
    unit_price: float | None
    tax: float | None
    line_total: float | None
    validation_status: str

    class Config:
        from_attributes = True

class ExtractionRunOut(BaseModel):
    id: str
    document_id: str
    entity_count: int
    fact_count: int
    line_item_count: int
    invalid_fact_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True