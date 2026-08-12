# ===== app/models/chunk.py =====
from sqlalchemy import String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class Chunk(BaseModel):
    __tablename__ = "chunks"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_type: Mapped[str] = mapped_column(String)  # header, line_items, section, table, clause, generic
    content: Mapped[str] = mapped_column(String)
    section_name: Mapped[str] = mapped_column(String, nullable=True)
    pages: Mapped[list] = mapped_column(JSON, default=list)
    block_ids: Mapped[list] = mapped_column(JSON, default=list)
    heading_path: Mapped[list] = mapped_column(JSON, default=list)  # ["Section 2", "Subsection 2.1"]
    token_count: Mapped[int] = mapped_column(Integer)
    char_count: Mapped[int] = mapped_column(Integer)
    prev_chunk_id: Mapped[str] = mapped_column(String, nullable=True)
    next_chunk_id: Mapped[str] = mapped_column(String, nullable=True)
    parent_section_id: Mapped[str] = mapped_column(String, nullable=True)
    chunker_name: Mapped[str] = mapped_column(String)
    chunk_version: Mapped[str] = mapped_column(String, default="1.0")
    validation_status: Mapped[str] = mapped_column(String, default="valid")

class ChunkingRun(BaseModel):
    __tablename__ = "chunking_runs"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunker_used: Mapped[str] = mapped_column(String)
    chunk_count: Mapped[int] = mapped_column(default=0)
    invalid_chunk_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String, default="completed")