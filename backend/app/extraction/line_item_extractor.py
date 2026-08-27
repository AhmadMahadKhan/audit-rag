
# ===== app/extraction/line_item_extractor.py =====
"""Extracts line items from canonical tables — heuristic column detection
by header keyword matching. Works for well-formed invoice/receipt tables."""
from app.canonical.schema import CanonicalDocument
from app.extraction.schema import ExtractedLineItem

COLUMN_HINTS = {
    "item_name": ["item", "description", "product"], "quantity": ["qty", "quantity"],
    "unit_price": ["unit price", "price", "rate"], "tax": ["tax", "vat"],
    "discount": ["discount"], "line_total": ["total", "amount"],
}

class LineItemExtractor:
    def extract(self, doc: CanonicalDocument) -> list[ExtractedLineItem]:
        items = []
        for table in doc.tables:
            if table.row_count < 2:
                continue
            header_row = [c for c in table.cells if c.row == 0]
            col_map = {}
            for cell in header_row:
                for field, hints in COLUMN_HINTS.items():
                    if any(h in cell.text.lower() for h in hints):
                        col_map[cell.col] = field

            rows: dict[int, dict] = {}
            for cell in table.cells:
                if cell.row == 0:
                    continue
                field = col_map.get(cell.col)
                if field:
                    rows.setdefault(cell.row, {})[field] = cell.text

            for row_idx, fields in rows.items():
                items.append(ExtractedLineItem(
                    table_id=table.table_id, row_index=row_idx,
                    item_name=fields.get("item_name"), description=fields.get("item_name"),
                    quantity=self._num(fields.get("quantity")), unit_price=self._num(fields.get("unit_price")),
                    tax=self._num(fields.get("tax")), discount=self._num(fields.get("discount")),
                    line_total=self._num(fields.get("line_total")),
                ))
        if not items:
            import re
            for b in doc.blocks:
                for line in b.text.split("\n"):
                    m = re.search(r"^([A-Za-z0-9\s\-]+?)\s+(\d+)\s+([\$\d\.,]+)\s+([\$\d\.,]+)$", line.strip())
                    if m and "qty" not in line.lower() and "total" not in line.lower() and "subtotal" not in line.lower():
                        items.append(ExtractedLineItem(
                            table_id="text_table", row_index=len(items) + 1,
                            item_name=m.group(1).strip(), description=m.group(1).strip(),
                            quantity=self._num(m.group(2)), unit_price=self._num(m.group(3)),
                            line_total=self._num(m.group(4)),
                        ))
        return items

    def _num(self, val: str | None) -> float | None:
        if not val:
            return None
        try:
            return float(val.replace(",", "").replace("$", "").strip())
        except ValueError:
            return None