# ===== app/rule_engine/rules/policy_rules.py =====
from app.rule_engine.base import BaseRule, RuleContext, RuleResult

class RequiredSectionMissingRule(BaseRule):
    key = "required_section_missing"
    name = "Required Policy Section Missing"
    category = "policy"
    default_severity = "medium"
    applicable_document_types = ["policy"]

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        required = ctx.config.get("required_sections", ["purpose", "scope", "policy"])
        text_lower = ctx.raw_text.lower()
        missing = [s for s in required if s not in text_lower]
        return RuleResult(self.key, triggered=bool(missing), severity=self.default_severity,
                           description=f"Missing required section(s): {missing}" if missing else "All required sections present",
                           evidence={"missing_sections": missing})