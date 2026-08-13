# ===== app/retrieval/filter_extractor.py =====
"""Extracts structured filters (document_type, vendor, date range) from
natural language query text, so users don't need a separate filter UI."""
import re
from dateutil import parser as date_parser

DOC_TYPE_HINTS = {"invoice": "invoice", "contract": "contract", "receipt": "receipt", "policy": "policy"}

def extract_filters(query: str) -> dict:
    filters = {}
    q_lower = query.lower()

    for hint, doc_type in DOC_TYPE_HINTS.items():
        if hint in q_lower:
            filters["document_type"] = doc_type
            break

    vendor_match = re.search(r"(?:from|with|to)\s+([A-Z][A-Za-z0-9&.\s]{2,30})", query)
    if vendor_match:
        filters["vendor"] = vendor_match.group(1).strip()

    return filters
