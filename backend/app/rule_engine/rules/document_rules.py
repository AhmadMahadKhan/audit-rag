# ===== app/rule_engine/rules/document_rules.py =====
from app.rule_engine.base import BaseRule, RuleContext, RuleResult

class MissingInvoiceNumberRule(BaseRule):
    key = "missing_invoice_number"
    name = "Missing Invoice Number"
    category = "document"
    default_severity = "high"
    applicable_document_types = ["invoice"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_invoice_number = any(e.get("entity_type") == "invoice_number" for e in ctx.entities)
        return RuleResult(self.key, triggered=not has_invoice_number, severity=self.default_severity,
                           description="Invoice number is missing" if not has_invoice_number else "Invoice number present",
                           recommendation="Request corrected invoice with invoice number" if not has_invoice_number else None)

class MissingVendorRule(BaseRule):
    key = "missing_vendor"
    name = "Missing Vendor"
    category = "document"
    default_severity = "medium"
    applicable_document_types = ["invoice", "receipt", "purchase_order"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_vendor = "vendor" in ctx.metadata and bool(ctx.metadata.get("vendor"))
        return RuleResult(self.key, triggered=not has_vendor, severity=self.default_severity,
                           description="Vendor not identified" if not has_vendor else "Vendor identified",
                           evidence={"vendor": ctx.metadata.get("vendor")})

class EmptyDocumentRule(BaseRule):
    key = "empty_document"
    name = "Empty Document"
    category = "document"
    default_severity = "critical"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        is_empty = len(ctx.raw_text.strip()) < 20
        return RuleResult(self.key, triggered=is_empty, severity=self.default_severity,
                           description="Document contains little or no extractable text")

class LowOCRConfidenceRule(BaseRule):
    key = "low_ocr_confidence"
    name = "Low OCR Confidence"
    category = "document"
    default_severity = "medium"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        blocks = (ctx.canonical or {}).get("blocks", [])
        ocr_confidences = [b["confidence"] for b in blocks if b.get("confidence") is not None]
        avg_conf = sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 1.0
        threshold = ctx.config.get("min_ocr_confidence", 0.6)
        triggered = bool(ocr_confidences) and avg_conf < threshold
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Average OCR confidence {avg_conf:.2f} below threshold {threshold}",
                           evidence={"avg_confidence": avg_conf}, confidence=avg_conf)

class MissingSignatureRule(BaseRule):
    key = "missing_signature"
    name = "Missing Signature"
    category = "document"
    default_severity = "high"
    applicable_document_types = ["contract"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_sig = "signature" in ctx.raw_text.lower() or "signed" in ctx.raw_text.lower()
        return RuleResult(self.key, triggered=not has_sig, severity=self.default_severity,
                           description="No signature block detected" if not has_sig else "Signature reference found")
