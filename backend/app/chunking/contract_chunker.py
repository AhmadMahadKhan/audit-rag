
# ===== app/chunking/contract_chunker.py =====
from app.chunking.base import BaseChunker
from app.chunking.schema import ChunkCandidate
from app.canonical.schema import CanonicalDocument

SECTION_HEADINGS = ["parties", "definitions", "scope", "payment terms", "obligations",
                     "confidentiality", "termination", "signatures"]

class ContractChunker(BaseChunker):
    """Chunks strictly by heading blocks — never splits mid-clause."""
    name = "contract_chunker"

    def chunk(self, doc: CanonicalDocument) -> list[ChunkCandidate]:
        candidates = []
        current_section, buffer, pages, blocks = "Preamble", [], set(), []

        def flush():
            if buffer:
                candidates.append(ChunkCandidate(
                    chunk_type="clause", content="\n".join(buffer), section_name=current_section,
                    pages=sorted(pages), block_ids=blocks, heading_path=[current_section],
                ))

        for block in sorted(doc.blocks, key=lambda b: (b.page, b.order)):
            if block.type == "heading":
                flush()
                current_section, buffer, pages, blocks = block.text, [], set(), []
            buffer.append(block.text)
            pages.add(block.page)
            blocks.append(block.block_id)
        flush()
        return candidates
