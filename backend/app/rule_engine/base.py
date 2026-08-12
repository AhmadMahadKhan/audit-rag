# ===== app/rule_engine/base.py =====
"""Every rule's evaluate() is pure/deterministic given the same RuleContext —
required for the spec's reproducibility guarantee."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class RuleContext:
    document_id: str
    document_type: str
    canonical: dict | None = None       # CanonicalDocument.model_dump()
    metadata: dict = field(default_factory=dict)   # {key: value}
    entities: list = field(default_factory=list)   # list of Entity ORM rows (or dicts)
    facts: dict = field(default_factory=dict)      # {fact_type: numeric_value}
    facts_raw: list = field(default_factory=list)  # list of Fact rows
    line_items: list = field(default_factory=list)
    raw_text: str = ""
    config: dict = field(default_factory=dict)     # per-rule config from RuleDefinition
    history: dict = field(default_factory=dict)    # cross-document lookups (duplicates etc.) — injected by service

@dataclass
class RuleResult:
    rule_key: str
    triggered: bool
    severity: str
    description: str
    evidence: dict = field(default_factory=dict)
    confidence: float = 1.0
    recommendation: str | None = None

class BaseRule(ABC):
    key: str = "base_rule"
    name: str = "Base Rule"
    category: str = "document"
    default_severity: str = "medium"
    applicable_document_types: list[str] = []  # empty = all

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> RuleResult: ...

    def applies_to(self, document_type: str) -> bool:
        return not self.applicable_document_types or document_type in self.applicable_document_types
