
# ===== app/rule_engine/rules/metadata_rules.py =====
from app.rule_engine.base import BaseRule, RuleContext, RuleResult
from datetime import date

class InvalidCurrencyRule(BaseRule):
    key = "invalid_currency"
    name = "Invalid Currency"
    category = "metadata"
    default_severity = "medium"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        import pycountry
        currency = ctx.metadata.get("currency")
        valid = {c.alpha_3 for c in pycountry.currencies}
        triggered = bool(currency) and currency not in valid
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Currency code '{currency}' not recognized" if triggered else "Currency valid",
                           evidence={"currency": currency})

class FutureDateRule(BaseRule):
    key = "future_transaction_date"
    name = "Future Transaction Date"
    category = "metadata"
    default_severity = "high"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        doc_date = ctx.metadata.get("invoice_date") or ctx.metadata.get("document_date")
        triggered = False
        if doc_date:
            try:
                parsed = date.fromisoformat(doc_date)
                triggered = parsed > date.today()
            except ValueError:
                pass
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Document date {doc_date} is in the future" if triggered else "Date not in future",
                           evidence={"date": doc_date})

class MissingCompanyRule(BaseRule):
    key = "missing_company"
    name = "Missing Company"
    category = "metadata"
    default_severity = "low"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_company = any(k in ctx.metadata for k in ("company", "vendor", "customer"))
        return RuleResult(self.key, triggered=not has_company, severity=self.default_severity,
                           description="No company/vendor/customer identified" if not has_company else "Company identified")
