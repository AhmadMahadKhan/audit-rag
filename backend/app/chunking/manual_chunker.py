# ===== app/chunking/manual_chunker.py =====
from app.chunking.policy_chunker import PolicyChunker

class ManualChunker(PolicyChunker):
    """Instructional docs share hierarchical structure with policies — reuse."""
    name = "manual_chunker"
