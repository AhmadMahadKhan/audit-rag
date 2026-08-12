
# ===== app/chunking/registry.py =====
from app.chunking.invoice_chunker import InvoiceChunker
from app.chunking.receipt_chunker import ReceiptChunker
from app.chunking.contract_chunker import ContractChunker
from app.chunking.policy_chunker import PolicyChunker
from app.chunking.manual_chunker import ManualChunker
from app.chunking.generic_chunker import GenericChunker

CHUNKER_MAP = {
    "invoice": InvoiceChunker, "receipt": ReceiptChunker, "purchase_order": InvoiceChunker,
    "contract": ContractChunker, "policy": PolicyChunker, "manual": ManualChunker,
}

def get_chunker(document_type: str) -> object:
    chunker_cls = CHUNKER_MAP.get(document_type, GenericChunker)
    return chunker_cls()