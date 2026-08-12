
# ===== app/schemas/rule_engine.py =====
from pydantic import BaseModel
from datetime import datetime

class RuleDefinitionOut(BaseModel):
    id: str
    rule_key: str
    name: str
    category: str
    severity: str
    version: int
    is_active: bool
    config: dict

    class Config:
        from_attributes = True

class RuleConfigUpdate(BaseModel):
    config: dict

class RuleFindingOut(BaseModel):
    id: str
    rule_key: str
    rule_name: str
    category: str
    severity: str
    triggered: bool
    description: str
    evidence: dict
    confidence: float
    recommendation: str | None

    class Config:
        from_attributes = True

class RuleExecutionRunOut(BaseModel):
    id: str
    document_id: str
    rules_executed: int
    rules_triggered: int
    rules_failed: int
    risk_score: float
    risk_level: str
    review_route: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
