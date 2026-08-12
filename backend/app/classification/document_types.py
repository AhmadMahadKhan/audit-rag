# ===== app/classification/document_types.py =====
"""Central registry — add new types here without touching classifier logic."""
DOCUMENT_TYPES = {
    "invoice": "invoice_pipeline",
    "receipt": "receipt_pipeline",
    "purchase_order": "purchase_order_pipeline",
    "bank_statement": "bank_statement_pipeline",
    "financial_statement": "financial_statement_pipeline",
    "tax_document": "tax_document_pipeline",
    "contract": "contract_pipeline",
    "policy": "policy_pipeline",
    "manual": "manual_pipeline",
    "audit_report": "audit_report_pipeline",
    "hr_document": "hr_document_pipeline",
    "email": "email_pipeline",
    "html": "generic_pipeline",
    "spreadsheet": "generic_pipeline",
    "presentation": "generic_pipeline",
    "unknown": "generic_pipeline",
}

def get_pipeline(document_type: str) -> str:
    return DOCUMENT_TYPES.get(document_type, "generic_pipeline")
