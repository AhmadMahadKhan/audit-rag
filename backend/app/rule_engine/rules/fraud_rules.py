# ===== app/rule_engine/rules/fraud_rules.py =====
"""Fraud rules generate structured findings/indicators — NOT final fraud
determinations, per spec ("should generate structured findings rather than
making final fraud determinations")."""
from app.rule_engine.base import BaseRule, RuleContext, RuleResult
from datetime import date

class RoundNumberPaymentRule(BaseRule):
    key = "round_number_payment"
    name = "Round Number Payment"
    category = "fraud"
    default_severity = "low"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        total = ctx.facts.get("invoice_total")
        triggered = total is not None and total > 0 and total % 100 == 0
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Round-number payment amount: {total}" if triggered else "Not a round number",
                           evidence={"amount": total},
                           recommendation="Review for potential manual entry or invoice splitting" if triggered else None)

class WeekendTransactionRule(BaseRule):
    key = "weekend_transaction"
    name = "Weekend Transaction"
    category = "fraud"
    default_severity = "low"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        doc_date = ctx.metadata.get("invoice_date") or ctx.metadata.get("document_date")
        triggered = False
        if doc_date:
            try:
                triggered = date.fromisoformat(doc_date).weekday() >= 5
            except ValueError:
                pass
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description="Transaction dated on a weekend" if triggered else "Weekday transaction")

class HighValueTransactionRule(BaseRule):
    key = "high_value_transaction"
    name = "High-Value Transaction"
    category = "fraud"
    default_severity = "medium"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        total = ctx.facts.get("invoice_total")
        threshold = ctx.config.get("high_value_threshold", 50000.0)
        triggered = total is not None and total > threshold
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Transaction value {total} exceeds high-value threshold {threshold}" if triggered else "Normal value",
                           evidence={"amount": total, "threshold": threshold})

class InvoiceSplittingRule(BaseRule):
    """Needs cross-document context — same vendor, multiple invoices just
    under approval threshold in a short window. Executor injects history."""
    key = "invoice_splitting"
    name = "Possible Invoice Splitting"
    category = "fraud"
    default_severity = "high"
    applicable_document_types = ["invoice"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        related = ctx.history.get("near_threshold_invoices_same_vendor", [])
        triggered = len(related) >= 2
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"{len(related)} similar sub-threshold invoices found from same vendor" if triggered else "No splitting pattern detected",
                           evidence={"related_documents": related})
