# ===== app/metadata/normalizer.py =====
import pycountry
from app.metadata.schema import MetadataField

def normalize_field(field: MetadataField) -> MetadataField:
    if field.key == "currency":
        field.value = field.value.strip().upper()
    elif field.key == "language":
        try:
            lang = pycountry.languages.get(alpha_2=field.value.lower())
            if lang:
                field.value = lang.alpha_2
        except Exception:
            pass
    elif "date" in field.key:
        field.value = field.value.strip()
    else:
        field.value = " ".join(field.value.split())  # collapse whitespace
    return field
