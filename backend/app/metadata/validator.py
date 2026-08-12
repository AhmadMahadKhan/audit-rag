# ===== app/metadata/validator.py =====
import pycountry
from app.metadata.schema import MetadataField

VALID_CURRENCIES = {c.alpha_3 for c in pycountry.currencies}

def validate_field(field: MetadataField) -> tuple[str, str | None]:
    """Returns (status, issue)."""
    if not field.value or not field.value.strip():
        return "invalid", "empty value"
    if field.key == "currency" and field.value not in VALID_CURRENCIES:
        return "needs_review", f"unrecognized currency code: {field.value}"
    if "date" in field.key:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", field.value):
            return "needs_review", "date not in ISO format"
    if field.confidence < 0.6:
        return "needs_review", "low confidence"
    return "valid", None