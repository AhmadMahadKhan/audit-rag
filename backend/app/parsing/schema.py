# ===== app/parsing/schema.py =====
"""Unified intermediate representation — every parser outputs this shape."""
from pydantic import BaseModel

class BoundingBox(BaseModel):
    page: int
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    confidence: float | None = None

class Block(BaseModel):
    block_id: str
    type: str  # heading, paragraph, table, list, image, caption, footer, header
    text: str = ""
    page: int
    order: int
    bbox: BoundingBox | None = None
    confidence: float | None = None

class TableCell(BaseModel):
    row: int
    col: int
    text: str
    rowspan: int = 1
    colspan: int = 1

class ParsedTable(BaseModel):
    table_id: str
    page: int
    order: int
    cells: list[TableCell]
    bbox: BoundingBox | None = None

class ParsedImage(BaseModel):
    image_id: str
    page: int
    bbox: BoundingBox | None = None
    caption: str | None = None

class PageInfo(BaseModel):
    page_number: int
    width: float | None = None
    height: float | None = None
    is_scanned: bool = False

class ParsedDocument(BaseModel):
    document_id: str
    source_format: str
    parser_name: str
    parser_version: str
    pages: list[PageInfo]
    blocks: list[Block]
    tables: list[ParsedTable]
    images: list[ParsedImage]
    raw_text: str
    reading_order_applied: bool = False
    ocr_used: bool = False
    processing_time_ms: float | None = None
    warnings: list[str] = []