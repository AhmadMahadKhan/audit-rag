
# ===== app/rule_engine/registry.py =====
"""Rules self-register here — adding a rule class to this list is the only
code change needed; RuleDefinition rows (DB) control enable/disable/config."""
from app.rule_engine.rules.document_rules import (
    MissingInvoiceNumberRule, MissingVendorRule, EmptyDocumentRule, LowOCRConfidenceRule, MissingSignatureRule,
)
from app.rule_engine.rules.metadata_rules import InvalidCurrencyRule, FutureDateRule, MissingCompanyRule
from app.rule_engine.rules.financial_rules import (
    TotalEqualsSubtotalPlusTaxRule, NegativeInvoiceAmountRule, InvoiceExceedsApprovalThresholdRule, LineItemMathRule,
)
from app.rule_engine.rules.invoice_rules import MissingDueDateRule, InvoiceDateAfterDueDateRule, DuplicateInvoiceRule
from app.rule_engine.rules.contract_rules import MissingEffectiveDateRule, ExpiredContractRule, MissingTerminationClauseRule
from app.rule_engine.rules.policy_rules import RequiredSectionMissingRule
from app.rule_engine.rules.fraud_rules import (
    RoundNumberPaymentRule, WeekendTransactionRule, HighValueTransactionRule, InvoiceSplittingRule,
)

ALL_RULES = [
    MissingInvoiceNumberRule, MissingVendorRule, EmptyDocumentRule, LowOCRConfidenceRule, MissingSignatureRule,
    InvalidCurrencyRule, FutureDateRule, MissingCompanyRule,
    TotalEqualsSubtotalPlusTaxRule, NegativeInvoiceAmountRule, InvoiceExceedsApprovalThresholdRule, LineItemMathRule,
    MissingDueDateRule, InvoiceDateAfterDueDateRule, DuplicateInvoiceRule,
    MissingEffectiveDateRule, ExpiredContractRule, MissingTerminationClauseRule,
    RequiredSectionMissingRule,
    RoundNumberPaymentRule, WeekendTransactionRule, HighValueTransactionRule, InvoiceSplittingRule,
]

RULE_MAP = {cls.key: cls for cls in ALL_RULES}

def get_rule_class(rule_key: str):
    return RULE_MAP.get(rule_key)

def get_rules_for_document_type(document_type: str) -> list:
    return [cls for cls in ALL_RULES if not cls.applicable_document_types or document_type in cls.applicable_document_types]
