
# ===== app/rule_engine/rules/financial_rules.py =====
from app.rule_engine.base import BaseRule, RuleContext, RuleResult

class TotalEqualsSubtotalPlusTaxRule(BaseRule):
    key = "total_equals_subtotal_plus_tax"
    name = "Total = Subtotal + Tax"
    category = "financial"
    default_severity = "high"
    applicable_document_types = ["invoice", "receipt"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        total, subtotal, tax = ctx.facts.get("invoice_total"), ctx.facts.get("subtotal"), ctx.facts.get("tax_amount")
        if total is None or subtotal is None or tax is None:
            return RuleResult(self.key, triggered=False, severity=self.default_severity,
                               description="Insufficient data to validate total calculation", confidence=0.0)
        tolerance = ctx.config.get("tolerance_pct", 0.02)
        expected = subtotal + tax
        triggered = abs(expected - total) > tolerance * max(total, 1)
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Total {total} != subtotal {subtotal} + tax {tax} (expected {expected:.2f})" if triggered else "Total calculation valid",
                           evidence={"total": total, "subtotal": subtotal, "tax": tax})

class NegativeInvoiceAmountRule(BaseRule):
    key = "negative_invoice_amount"
    name = "Negative Invoice Amount"
    category = "financial"
    default_severity = "critical"
    applicable_document_types = ["invoice", "receipt", "purchase_order"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        total = ctx.facts.get("invoice_total")
        triggered = total is not None and total < 0
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Negative invoice total: {total}" if triggered else "Amount non-negative")

class InvoiceExceedsApprovalThresholdRule(BaseRule):
    key = "invoice_exceeds_approval_threshold"
    name = "Invoice Exceeds Approval Threshold"
    category = "financial"
    default_severity = "medium"
    applicable_document_types = ["invoice", "purchase_order"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        total = ctx.facts.get("invoice_total")
        limit = ctx.config.get("approval_limit", 10000.0)
        triggered = total is not None and total > limit
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Invoice total {total} exceeds approval limit {limit}" if triggered else "Within approval limit",
                           evidence={"total": total, "limit": limit})

class LineItemMathRule(BaseRule):
    key = "line_item_math_mismatch"
    name = "Line Item Quantity × Price Mismatch"
    category = "financial"
    default_severity = "medium"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        tolerance = ctx.config.get("tolerance_pct", 0.02)
        mismatches = []
        for item in ctx.line_items:
            qty, price, total = item.get("quantity"), item.get("unit_price"), item.get("line_total")
            if qty is not None and price is not None and total is not None:
                expected = qty * price
                if abs(expected - total) > tolerance * max(total, 1):
                    mismatches.append({"item": item.get("item_name"), "expected": expected, "actual": total})
        return RuleResult(self.key, triggered=bool(mismatches), severity=self.default_severity,
                           description=f"{len(mismatches)} line item(s) with quantity×price mismatch" if mismatches else "Line items consistent",
                           evidence={"mismatches": mismatches})