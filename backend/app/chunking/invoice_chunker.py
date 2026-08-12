
# ===== app/chunking/invoice_chunker.py =====
from app.chunking.base import BaseChunker
from app.chunking.schema import ChunkCandidate
from app.chunking.table_chunker import TableChunker
from app.canonical.schema import CanonicalDocument

HEADER_KEYWORDS = ["invoice", "vendor", "from"]
CUSTOMER_KEYWORDS = ["bill to", "customer", "client"]
PAYMENT_KEYWORDS = ["payment", "due date", "terms"]
TOTAL_KEYWORDS = ["total", "subtotal", "tax"]

class InvoiceChunker(BaseChunker):
    """Groups blocks by semantic invoice section rather than fixed token windows."""
    name = "invoice_chunker"

    def chunk(self, doc: CanonicalDocument) -> list[ChunkCandidate]:
        sections = {"header": [], "customer": [], "payment": [], "totals": [], "other": []}
        section_pages = {k: set() for k in sections}
        section_blocks = {k: [] for k in sections}

        for block in sorted(doc.blocks, key=lambda b: (b.page, b.order)):
            text_lower = block.text.lower()
            key = "other"
            if any(k in text_lower for k in HEADER_KEYWORDS):
                key = "header"
            elif any(k in text_lower for k in CUSTOMER_KEYWORDS):
                key = "customer"
            elif any(k in text_lower for k in PAYMENT_KEYWORDS):
                key = "payment"
            elif any(k in text_lower for k in TOTAL_KEYWORDS):
                key = "totals"
            sections[key].append(block.text)
            section_pages[key].add(block.page)
            section_blocks[key].append(block.block_id)

        candidates = []
        for key, texts in sections.items():
            if texts:
                candidates.append(ChunkCandidate(
                    chunk_type=key, content="\n".join(texts), section_name=key.capitalize(),
                    pages=sorted(section_pages[key]), block_ids=section_blocks[key], heading_path=[key.capitalize()],
                ))

        table_chunker = TableChunker()
        for table in doc.tables:
            candidates.extend(table_chunker.chunk_table(doc.info.document_id, table))
        return candidates