
# ===== app/chunking/schema.py =====
from pydantic import BaseModel

class ChunkCandidate(BaseModel):
    chunk_type: str
    content: str
    section_name: str | None = None
    pages: list[int] = []
    block_ids: list[str] = []
    heading_path: list[str] = []