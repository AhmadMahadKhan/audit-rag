
# ===== app/extraction/validator.py =====
TOLERANCE = 0.02  # allow small rounding differences

def validate_facts(facts: dict[str, float]) -> list[tuple[str, str]]:
    """facts: {fact_type: numeric_value}. Returns [(fact_type, issue)]."""
    issues = []
    total, subtotal, tax = facts.get("invoice_total"), facts.get("subtotal"), facts.get("tax_amount")
    if total is not None and subtotal is not None and tax is not None:
        expected = subtotal + tax
        if abs(expected - total) > TOLERANCE * max(total, 1):
            issues.append(("invoice_total", f"Total {total} != subtotal {subtotal} + tax {tax}"))
    if total is not None and total < 0:
        issues.append(("invoice_total", "Negative invoice amount"))
    return issues

def validate_line_item(item) -> str | None:
    if item.quantity is not None and item.unit_price is not None and item.line_total is not None:
        expected = item.quantity * item.unit_price - (item.discount or 0)
        if abs(expected - item.line_total) > TOLERANCE * max(item.line_total, 1):
            return f"quantity*unit_price ({expected:.2f}) != line_total ({item.line_total})"
    return None
