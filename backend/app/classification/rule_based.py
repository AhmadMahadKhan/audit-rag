import re
from app.classification.base import BaseClassifier, ClassificationResult
from app.classification.document_types import DOCUMENT_TYPES

FILENAME_PATTERNS = {
    "invoice": r"invoice|inv[-_]?\d+",
    "receipt": r"receipt|rcpt",
    "purchase_order": r"purchase[-_]?order|\bpo[-_]?\d+",
    "bank_statement": r"bank[-_]?statement|statement",
    "tax_document": r"tax|w-?2|1099",
    "contract": r"contract|agreement|nda",
    "policy": r"policy|policies",
    "manual": r"manual|guide|handbook",
    "audit_report": r"audit",
    "hr_document": r"hr[-_]|employee|payroll",
}

MIME_TYPE_HINTS = {
    "message/rfc822": "email",
    "text/html": "html",
    "application/vnd.ms-excel": "spreadsheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "spreadsheet",
    "application/vnd.ms-powerpoint": "presentation",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "presentation",
}

class RuleBasedClassifier(BaseClassifier):
    async def classify(self, filename: str, mime_type: str, content: bytes) -> ClassificationResult:
        name_lower = filename.lower()

        for doc_type, pattern in FILENAME_PATTERNS.items():
            if re.search(pattern, name_lower):
                return ClassificationResult(document_type=doc_type, confidence=0.75, method="rule_based")

        if mime_type in MIME_TYPE_HINTS:
            return ClassificationResult(document_type=MIME_TYPE_HINTS[mime_type], confidence=0.65, method="rule_based")

        return ClassificationResult(document_type="unknown", confidence=0.3, method="rule_based")
