
# ===== app/vectorstore/factory.py =====
from app.vectorstore.qdrant_provider import QdrantProvider
from app.vectorstore.base import VectorStoreProvider

_instance: VectorStoreProvider | None = None

def get_vector_store() -> VectorStoreProvider:
    global _instance
    if _instance is None:
        _instance = QdrantProvider()
    return _instance
