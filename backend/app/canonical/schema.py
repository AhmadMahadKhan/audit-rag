"""
the schema every downstream module consumes.
"""
from pydantic import BaseModel, field_validator
from datetime import datetime

CDM_SCHEMA_VERSION = "1.0"

class BoundingBox(BaseModel):
    page: int
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    confidence: float | None = None

class DocumentInfo(BaseModel):
    document_id: str
    file_name: str
    file_type: str
    mime_type: str
    file_size: int
    file_hash: str
    parser_name: str
    parser_version: str
    schema_version: str = CDM_SCHEMA_VERSION
    processed_at: datetime
    language: str | None = None
    page_count: int

class PageModel(BaseModel):
    page_number: int
    width: float | None = None
    height: float | None = None
    rotation: float = 0.0
    ocr_confidence: float | None = None
    reading_order: list[str] = []  # ordered block_ids

class BlockModel(BaseModel):
    block_id: str
    type: str  # paragraph|heading|table|list|image|caption|footer|header|form|code|unknown
    text: str = ""
    page: int
    order: int
    bbox: BoundingBox | None = None
    confidence: float | None = None
    parent_block_id: str | None = None  # hierarchy: heading -> paragraph, etc.

class TableCellModel(BaseModel):
    row: int
    col: int
    text: str
    rowspan: int = 1
    colspan: int = 1
    is_header: bool = False

class TableModel(BaseModel):
    table_id: str
    page: int
    row_count: int
    col_count: int
    cells: list[TableCellModel]
    bbox: BoundingBox | None = None
    confidence: float | None = None

class ImageModel(BaseModel):
    image_id: str
    page: int
    bbox: BoundingBox | None = None
    caption: str | None = None
    image_type: str | None = None
    storage_ref: str | None = None

class EntityModel(BaseModel):
    """Populated in Phase 8 — schema-ready now."""
    entity_id: str
    entity_type: str
    text: str
    page: int | None = None
    block_id: str | None = None
    bbox: BoundingBox | None = None
    confidence: float | None = None

class RelationshipModel(BaseModel):
    relationship_id: str
    type: str  # parent_child, table_cell, image_caption, heading_paragraph, section_subsection
    source_id: str
    target_id: str

class ProcessingInfo(BaseModel):
    ocr_used: bool = False
    processing_time_ms: float | None = None
    warnings: list[str] = []
    validation_status: str = "valid"  # valid | invalid

class CanonicalDocument(BaseModel):
    info: DocumentInfo
    pages: list[PageModel]
    blocks: list[BlockModel]
    tables: list[TableModel]
    images: list[ImageModel]
    entities: list[EntityModel] = []       # empty until Phase 8
    relationships: list[RelationshipModel] = []
    raw_text: str
    processing: ProcessingInfo

    @field_validator("blocks")
    @classmethod
    def blocks_have_unique_ids(cls, v):
        ids = [b.block_id for b in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate block_id detected")
        return v
