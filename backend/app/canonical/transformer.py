# ===== app/canonical/transformer.py =====

import uuid
from datetime import datetime, timezone
from app.parsing.schema import ParsedDocument
from app.canonical.schema import (
    CanonicalDocument, DocumentInfo, PageModel, BlockModel, TableModel,
    TableCellModel, ImageModel, RelationshipModel, ProcessingInfo, BoundingBox,
)

def _bbox(b) -> BoundingBox | None:
    if not b:
        return None
    return BoundingBox(page=b.page, x=b.x, y=b.y, width=b.width, height=b.height,
                        rotation=b.rotation, confidence=b.confidence)

def transform_to_canonical(parsed: ParsedDocument, document_meta: dict) -> CanonicalDocument:
    """document_meta: {file_name, file_type, mime_type, file_size, file_hash}"""
    info = DocumentInfo(
        document_id=parsed.document_id, file_name=document_meta["file_name"],
        file_type=document_meta["file_type"], mime_type=document_meta["mime_type"],
        file_size=document_meta["file_size"], file_hash=document_meta["file_hash"],
        parser_name=parsed.parser_name, parser_version=parsed.parser_version,
        processed_at=datetime.now(timezone.utc), page_count=len(parsed.pages),
    )

    pages = [PageModel(page_number=p.page_number, width=p.width, height=p.height,
                        ocr_confidence=None, reading_order=[]) for p in parsed.pages]

    blocks = [BlockModel(block_id=b.block_id, type=b.type, text=b.text, page=b.page,
                          order=b.order, bbox=_bbox(b.bbox), confidence=b.confidence) for b in parsed.blocks]

    # populate reading_order per page from block order
    page_map = {p.page_number: p for p in pages}
    for b in sorted(blocks, key=lambda x: (x.page, x.order)):
        if b.page in page_map:
            page_map[b.page].reading_order.append(b.block_id)

    tables = []
    for t in parsed.tables:
        rows = {c.row for c in t.cells} or {0}
        cols = {c.col for c in t.cells} or {0}
        cells = [TableCellModel(row=c.row, col=c.col, text=c.text, rowspan=c.rowspan, colspan=c.colspan) for c in t.cells]
        tables.append(TableModel(table_id=t.table_id, page=t.page, row_count=max(rows) + 1,
                                   col_count=max(cols) + 1, cells=cells, bbox=_bbox(t.bbox)))

    images = [ImageModel(image_id=i.image_id, page=i.page, bbox=_bbox(i.bbox), caption=i.caption) for i in parsed.images]

    # simple heading->paragraph relationships as a starting hierarchy
    relationships = []
    last_heading = None
    for b in sorted(blocks, key=lambda x: (x.page, x.order)):
        if b.type == "heading":
            last_heading = b.block_id
        elif last_heading and b.type == "paragraph":
            relationships.append(RelationshipModel(
                relationship_id=str(uuid.uuid4()), type="heading_paragraph",
                source_id=last_heading, target_id=b.block_id,
            ))

    processing = ProcessingInfo(ocr_used=parsed.ocr_used, processing_time_ms=parsed.processing_time_ms,
                                  warnings=parsed.warnings, validation_status="valid")

    return CanonicalDocument(info=info, pages=pages, blocks=blocks, tables=tables, images=images,
                               entities=[], relationships=relationships, raw_text=parsed.raw_text, processing=processing)
