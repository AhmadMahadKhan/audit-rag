# ===== app/chunking/receipt_chunker.py =====
from app.chunking.invoice_chunker import InvoiceChunker

class ReceiptChunker(InvoiceChunker):
    """Receipts share invoice-like structure (merchant/items/totals) — reuse with different label."""
    name = "receipt_chunker"