# ===== app/extraction/fact_extractor.py =====
import re
from app.canonical.schema import CanonicalDocument
from app.extraction.schema import ExtractedFact

MONEY_LABELS = {
    "invoice_total": r"\btotal[:\s]+\$?([\d,]+\.?\d*)",
    "subtotal": r"sub\s*-?\s*total[:\s]+\$?([\d,]+\.?\d*)",
    "tax_amount": r"tax(?:\s*amount)?[:\s]+\$?([\d,]+\.?\d*)",
    "discount": r"discount[:\s]+\$?([\d,]+\.?\d*)",
}

# Financial-statement line items. Keys are canonical fact_type values;

FINANCIAL_STATEMENT_LABELS = {
    "revenue": ["total revenue", "net revenue", "revenue", "net sales", "total net sales"],
    "cost_of_revenue": ["cost of revenue", "cost of goods sold", "cost of sales"],
    "gross_profit": ["gross profit", "gross margin"],
    "operating_income": ["operating income", "income from operations"],
    "net_income": ["net income", "net earnings", "net profit"],
    "total_assets": ["total assets"],
    "total_liabilities": ["total liabilities"],
    "total_equity": ["total stockholders' equity", "total shareholders' equity", "total equity"],
    "cash_and_equivalents": ["cash and cash equivalents", "cash and equivalents"],
    "eps": ["earnings per share", "diluted earnings per share", "basic earnings per share"],
}

_NUMERIC_RE = re.compile(r"\(?\$?\s*([\d,]+\.?\d*)\)?")


def _parse_numeric(text: str) -> float | None:
    """Parses a table cell's numeric value. Treats parenthesized values
    as negative, per standard financial-statement convention."""
    if not text:
        return None
    match = _NUMERIC_RE.search(text)
    if not match:
        return None
    raw = match.group(1).replace(",", "")
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if "(" in text and ")" in text:
        value = -value
    return value


class FinancialFactExtractor:
    def extract(self, doc: CanonicalDocument) -> list[ExtractedFact]:
        facts = []

        # --- Table-driven extraction (preferred; requires RC1's populated tables) ---
        for table in doc.tables:
            facts.extend(self._extract_from_table(table))


        for fact_type, pattern in MONEY_LABELS.items():
            match = re.search(pattern, doc.raw_text, re.IGNORECASE)
            if match:
                raw_value = match.group(1).replace(",", "")
                try:
                    numeric = float(raw_value)
                    facts.append(ExtractedFact(
                        fact_type=fact_type, value=raw_value,
                        numeric_value=numeric, confidence=0.75,
                    ))
                except ValueError:
                    pass

        
        
        if not doc.tables:
            for fact_type, labels in FINANCIAL_STATEMENT_LABELS.items():
                for label in labels:
                    pattern = re.escape(label) + r"[:\s]+\$?\(?([\d,]+\.?\d*)\)?"
                    match = re.search(pattern, doc.raw_text, re.IGNORECASE)
                    if match:
                        raw_value = match.group(1).replace(",", "")
                        try:
                            numeric = float(raw_value)
                            facts.append(ExtractedFact(
                                fact_type=fact_type, value=raw_value,
                                numeric_value=numeric, confidence=0.5,  # lower: text-only, no table structure
                            ))
                        except ValueError:
                            pass
                        break  # first matching label variant wins per fact_type

        return facts

    def _extract_from_table(self, table) -> list[ExtractedFact]:
        facts = []
        rows: dict[int, dict[int, str]] = {}
        for cell in table.cells:
            rows.setdefault(cell.row, {})[cell.col] = cell.text

        for row_idx, row_cells in rows.items():
            if not row_cells:
                continue
            sorted_cols = sorted(row_cells.keys())
            label_col = sorted_cols[0]
            label_text = (row_cells.get(label_col) or "").strip().lower()
            if not label_text:
                continue

            fact_type = self._match_label(label_text)
            if not fact_type:
                continue

            # Take the rightmost non-empty numeric cell in the row as the value
            # (financial tables commonly show current period rightmost, or
            # multiple periods — rightmost is the most defensible single default).
            numeric_value = None
            raw_value = None
            for col in reversed(sorted_cols[1:]):
                candidate_text = row_cells.get(col, "")
                parsed = _parse_numeric(candidate_text)
                if parsed is not None:
                    numeric_value = parsed
                    raw_value = candidate_text.strip()
                    break

            if numeric_value is None:
                continue

            facts.append(ExtractedFact(
                fact_type=fact_type,
                value=raw_value,
                numeric_value=numeric_value,
                confidence=0.85,  # higher: table-structure-derived
            ))

        return facts

    @staticmethod
    def _match_label(label_text: str) -> str | None:
        for fact_type, variants in FINANCIAL_STATEMENT_LABELS.items():
            for variant in variants:
                if variant in label_text:
                    return fact_type
        return None