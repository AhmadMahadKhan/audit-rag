# ===== app/models/knowledge.py =====
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class Entity(BaseModel):
    __tablename__ = "entities"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String, index=True)  # organization, person, invoice_number, etc.
    value: Mapped[str] = mapped_column(String)
    canonical_value: Mapped[str] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    page: Mapped[int] = mapped_column(nullable=True)
    block_id: Mapped[str] = mapped_column(String, nullable=True)
    bbox: Mapped[dict] = mapped_column(JSON, nullable=True)
    method: Mapped[str] = mapped_column(String)  # rule_based | ai_based
    extractor_version: Mapped[str] = mapped_column(String)

class Fact(BaseModel):
    __tablename__ = "facts"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    fact_type: Mapped[str] = mapped_column(String, index=True)  # invoice_total, subtotal, tax_amount, effective_date...
    value: Mapped[str] = mapped_column(String)
    numeric_value: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="valid")  # valid | needs_review | invalid
    validation_note: Mapped[str] = mapped_column(String, nullable=True)
    source_entity_id: Mapped[str] = mapped_column(String, nullable=True)

class LineItem(BaseModel):
    __tablename__ = "line_items"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    table_id: Mapped[str] = mapped_column(String, nullable=True)
    row_index: Mapped[int] = mapped_column()
    item_name: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, nullable=True)
    tax: Mapped[float] = mapped_column(Float, nullable=True)
    discount: Mapped[float] = mapped_column(Float, nullable=True)
    line_total: Mapped[float] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str] = mapped_column(String, default="valid")

class KnowledgeRelationship(BaseModel):
    __tablename__ = "knowledge_relationships"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String)  # vendor_invoice, invoice_line_item, employee_department...
    source_type: Mapped[str] = mapped_column(String)  # entity | fact
    source_id: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)
    target_id: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

class ExtractionRun(BaseModel):
    __tablename__ = "extraction_runs"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    entity_count: Mapped[int] = mapped_column(default=0)
    fact_count: Mapped[int] = mapped_column(default=0)
    line_item_count: Mapped[int] = mapped_column(default=0)
    invalid_fact_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String, default="completed")
