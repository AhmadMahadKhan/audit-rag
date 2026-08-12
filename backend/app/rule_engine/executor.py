# ===== app/rule_engine/executor.py =====
"""Runs the applicable rule set with per-rule fault isolation (spec: 'single
broken rule should not stop the entire rule set') and basic parallelism."""
import asyncio
from app.rule_engine.base import RuleContext, RuleResult
from app.rule_engine.registry import get_rules_for_document_type, get_rule_class
from app.core.logging_config import logger

class RuleExecutionError(Exception):
    def __init__(self, rule_key: str, error: str):
        self.rule_key = rule_key
        self.error = error

async def execute_rules(ctx: RuleContext, active_rule_keys: set[str], rule_configs: dict[str, dict]) -> tuple[list[RuleResult], list[str]]:
    applicable = [cls for cls in get_rules_for_document_type(ctx.document_type) if cls.key in active_rule_keys]

    async def run_one(rule_cls):
        instance = rule_cls()
        rule_ctx = RuleContext(**{**ctx.__dict__, "config": rule_configs.get(rule_cls.key, {})})
        try:
            return await asyncio.wait_for(asyncio.to_thread(instance.evaluate, rule_ctx), timeout=10.0)
        except Exception as e:
            logger.error("rule_execution_failed", rule=rule_cls.key, error=str(e))
            return None

    results = await asyncio.gather(*(run_one(cls) for cls in applicable))
    successful = [r for r in results if r is not None]
    failed_keys = [applicable[i].key for i, r in enumerate(results) if r is None]
    return successful, failed_keys