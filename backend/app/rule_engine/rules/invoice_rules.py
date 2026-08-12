
# ===== app/rule_engine/rules/invoice_rules.py =====
from app.rule_engine.base import BaseRule, RuleContext, RuleResult

class MissingDueDateRule(BaseRule):
    key = "missing_due_date"
    name = "Missing Due Date"
    category = "invoice"
    default_severity = "low"
    applicable_document_types = ["invoice"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_due_date = "due_date" in ctx.metadata
        return RuleResult(self.key, triggered=not has_due_date, severity=self.default_severity,
                           description="Due date not found" if not has_due_date else "Due date present")

class InvoiceDateAfterDueDateRule(BaseRule):
    key = "invoice_date_after_due_date"
    name = "Invoice Date After Due Date"
    category = "invoice"
    default_severity = "high"
    applicable_document_types = ["invoice"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        from datetime import date
        inv_date, due_date = ctx.metadata.get("invoice_date"), ctx.metadata.get("due_date")
        triggered = False
        if inv_date and due_date:
            try:
                triggered = date.fromisoformat(inv_date) > date.fromisoformat(due_date)
            except ValueError:
                pass
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description="Invoice date is after due date" if triggered else "Date order valid",
                           evidence={"invoice_date": inv_date, "due_date": due_date})

class DuplicateInvoiceRule(BaseRule):
    """Relies on ctx.history['duplicate_invoice_numbers'] injected by the
    executor (cross-document lookup — a single rule can't see other docs)."""
    key = "duplicate_invoice"
    name = "Duplicate Invoice"
    category = "invoice"
    default_severity = "critical"
    applicable_document_types = ["invoice"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        duplicates = ctx.history.get("duplicate_invoice_numbers", [])
        triggered = bool(duplicates)
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Invoice number also found in document(s): {duplicates}" if triggered else "No duplicate found",
                           evidence={"duplicate_documents": duplicates})
