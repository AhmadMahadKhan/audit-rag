
# ===== app/canonical/validator.py =====
from app.canonical.schema import CanonicalDocument

class SchemaValidationError(Exception):
    pass

def validate_canonical_document(doc: CanonicalDocument) -> list[str]:
    """Returns list of issues; empty list = valid. Pydantic already enforces
    types/required fields — this covers cross-field reference integrity."""
    issues = []
    page_numbers = {p.page_number for p in doc.pages}

    for block in doc.blocks:
        if block.page not in page_numbers:
            issues.append(f"Block {block.block_id} references missing page {block.page}")
        if block.bbox and block.bbox.page != block.page:
            issues.append(f"Block {block.block_id} bbox page mismatch")

    for table in doc.tables:
        if table.page not in page_numbers:
            issues.append(f"Table {table.table_id} references missing page {table.page}")
        expected_cells = table.row_count * table.col_count
        if len(table.cells) > expected_cells:
            issues.append(f"Table {table.table_id} has more cells than row_count*col_count implies")

    for img in doc.images:
        if img.page not in page_numbers:
            issues.append(f"Image {img.image_id} references missing page {img.page}")

    block_ids = {b.block_id for b in doc.blocks}
    for rel in doc.relationships:
        if rel.source_id not in block_ids and rel.source_id not in {t.table_id for t in doc.tables}:
            issues.append(f"Relationship {rel.relationship_id} has unknown source_id {rel.source_id}")

    if doc.info.schema_version != "1.0":
        issues.append(f"Unsupported schema version: {doc.info.schema_version}")

    return issues