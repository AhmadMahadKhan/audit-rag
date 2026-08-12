
# ===== app/chunking/policy_chunker.py =====
from app.chunking.base import BaseChunker
from app.chunking.schema import ChunkCandidate
from app.canonical.schema import CanonicalDocument

class PolicyChunker(BaseChunker):
    """Maintains heading hierarchy (Section > Subsection) via block.parent_block_id
    relationships """
    name = "policy_chunker"

    def chunk(self, doc: CanonicalDocument) -> list[ChunkCandidate]:
        heading_stack: list[str] = []
        candidates = []
        buffer, pages, blocks = [], set(), []

        def flush():
            if buffer:
                candidates.append(ChunkCandidate(
                    chunk_type="section", content="\n".join(buffer),
                    section_name=heading_stack[-1] if heading_stack else None,
                    pages=sorted(pages), block_ids=blocks, heading_path=list(heading_stack),
                ))

        for block in sorted(doc.blocks, key=lambda b: (b.page, b.order)):
            if block.type == "heading":
                flush()
                heading_stack = [block.text]  # simplified: real hierarchy depth needs heading-level metadata
                buffer, pages, blocks = [], set(), []
            buffer.append(block.text)
            pages.add(block.page)
            blocks.append(block.block_id)
        flush()
        return candidates
