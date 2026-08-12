
# ===== app/chunking/table_chunker.py =====
from app.chunking.schema import ChunkCandidate
from app.chunking.token_utils import estimate_tokens
from app.canonical.schema import CanonicalDocument, TableModel

MAX_ROWS_PER_CHUNK = 25

class TableChunker:
    name = "table_chunker"

    def chunk_table(self, doc_id: str, table: TableModel) -> list[ChunkCandidate]:
        headers = {c.col: c.text for c in table.cells if c.row == 0}
        rows: dict[int, dict[int, str]] = {}
        for c in table.cells:
            if c.row == 0:
                continue
            rows.setdefault(c.row, {})[c.col] = c.text

        row_indices = sorted(rows.keys())
        candidates = []
        for i in range(0, len(row_indices), MAX_ROWS_PER_CHUNK):
            batch = row_indices[i:i + MAX_ROWS_PER_CHUNK]
            lines = [" | ".join(headers.get(col, "") for col in sorted(headers))]
            for r in batch:
                lines.append(" | ".join(rows[r].get(col, "") for col in sorted(headers)))
            candidates.append(ChunkCandidate(
                chunk_type="table", content="\n".join(lines), section_name=f"Table {table.table_id}",
                pages=[table.page], block_ids=[table.table_id],
                heading_path=[f"Table {table.table_id} (rows {batch[0]}-{batch[-1]})"],
            ))
        return candidates