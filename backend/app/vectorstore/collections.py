
# ===== app/vectorstore/collections.py =====
"""Collection naming/registry — one collection per embedding type keeps
payload schemas homogeneous and filters cheap."""
COLLECTIONS = {
    "text": "doc_chunks",
    "table": "table_embeddings",
    "metadata": "metadata_embeddings",
    "entity": "entity_embeddings",
    "summary": "summary_embeddings",
}

def collection_for(embedding_type: str) -> str:
    name = COLLECTIONS.get(embedding_type)
    if not name:
        raise ValueError(f"No collection mapped for embedding type: {embedding_type}")
    return name