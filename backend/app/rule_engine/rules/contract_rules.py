
# ===== app/rule_engine/rules/contract_rules.py =====
from app.rule_engine.base import BaseRule, RuleContext, RuleResult

class MissingEffectiveDateRule(BaseRule):
    key = "missing_effective_date"
    name = "Missing Effective Date"
    category = "contract"
    default_severity = "medium"
    applicable_document_types = ["contract"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_date = "effective_date" in ctx.metadata
        return RuleResult(self.key, triggered=not has_date, severity=self.default_severity,
                           description="Effective date not found" if not has_date else "Effective date present")

class ExpiredContractRule(BaseRule):
    key = "expired_contract"
    name = "Expired Contract"
    category = "contract"
    default_severity = "high"
    applicable_document_types = ["contract"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        from datetime import date
        expiry = ctx.metadata.get("expiration_date")
        triggered = False
        if expiry:
            try:
                triggered = date.fromisoformat(expiry) < date.today()
            except ValueError:
                pass
        return RuleResult(self.key, triggered=triggered, severity=self.default_severity,
                           description=f"Contract expired on {expiry}" if triggered else "Contract not expired")

class MissingTerminationClauseRule(BaseRule):
    key = "missing_termination_clause"
    name = "Missing Termination Clause"
    category = "contract"
    default_severity = "low"
    applicable_document_types = ["contract"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        has_clause = "terminat" in ctx.raw_text.lower()
        return RuleResult(self.key, triggered=not has_clause, severity=self.default_severity,
                           description="No termination clause detected" if not has_clause else "Termination clause found")
