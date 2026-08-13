
# ===== app/vectorstore/payload_builder.py =====
"""Builds the rich Qdrant payload so filtered search never needs a Postgres round-trip."""
from datetime import datetime, timezone

def build_payload(embedding_record, document, chunk=None, metadata_fields=None) -> dict:
    payload = {
        "document_id": embedding_record.document_id,
        "chunk_id": embedding_record.chunk_id,
        "embedding_type": embedding_record.embedding_type,
        "document_type": document.document_type,
        "model_name": embedding_record.model_name,
        "model_version": embedding_record.model_version,
        "embedding_version": embedding_record.model_version,
        "processing_timestamp": datetime.now(timezone.utc).timestamp(),
    }
    if chunk:
        payload.update({
            "pages": chunk.pages, "section_name": chunk.section_name,
            "heading_path": chunk.heading_path, "chunk_type": chunk.chunk_type,
        })
    if metadata_fields:
        for f in metadata_fields:
            if f.key in ("vendor", "customer", "company", "department", "currency", "language"):
                payload[f.key] = f.value
    return payload