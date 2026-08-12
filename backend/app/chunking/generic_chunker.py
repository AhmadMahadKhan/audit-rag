

# ===== app/chunking/generic_chunker.py =====
from app.chunking.base import BaseChunker
from app.chunking.schema import ChunkCandidate
from app.chunking.token_utils import estimate_tokens
from app.canonical.schema import CanonicalDocument

class GenericChunker(BaseChunker):
    """Fallback: groups consecutive blocks up to max_tokens, with overlap.
    Used for manuals, unknown types, and anything without a specialized chunker."""
    name = "generic_chunker"

    def chunk(self, doc: CanonicalDocument) -> list[ChunkCandidate]:
        candidates = []
        buffer_text, buffer_pages, buffer_blocks = [], set(), []
        current_heading = None

        def flush():
            if buffer_text:
                candidates.append(ChunkCandidate(
                    chunk_type="generic", content="\n".join(buffer_text),
                    section_name=current_heading, pages=sorted(buffer_pages), block_ids=list(buffer_blocks),
                    heading_path=[current_heading] if current_heading else [],
                ))

        token_total = 0
        for block in sorted(doc.blocks, key=lambda b: (b.page, b.order)):
            if block.type == "heading":
                flush()
                buffer_text, buffer_pages, buffer_blocks = [], set(), []
                token_total = 0
                current_heading = block.text

            block_tokens = estimate_tokens(block.text)
            if token_total + block_tokens > self.max_tokens and buffer_text:
                flush()
                # overlap: carry last ~overlap_tokens worth of text forward
                overlap_text = buffer_text[-1] if buffer_text else ""
                buffer_text, buffer_pages, buffer_blocks = [overlap_text] if overlap_text else [], set(), []
                token_total = estimate_tokens(overlap_text)

            buffer_text.append(block.text)
            buffer_pages.add(block.page)
            buffer_blocks.append(block.block_id)
            token_total += block_tokens

        flush()
        return candidates