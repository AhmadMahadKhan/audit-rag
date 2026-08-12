# ===== app/parsing/text_parser.py =====
import time
from app.parsing.base import BaseParser
from app.parsing.schema import ParsedDocument, PageInfo, Block

class TextParser(BaseParser):
    name = "text_parser"
    version = "1.0"

    async def parse(self, document_id: str, content: bytes) -> ParsedDocument:
        t0 = time.perf_counter()
        text = content.decode("utf-8", errors="replace")
        blocks = [
            Block(block_id=f"{document_id}_b{i}", type="paragraph", text=line.strip(), page=1, order=i)
            for i, line in enumerate(text.splitlines()) if line.strip()
        ]
        return ParsedDocument(
            document_id=document_id, source_format="txt", parser_name=self.name, parser_version=self.version,
            pages=[PageInfo(page_number=1)], blocks=blocks, tables=[], images=[],
            raw_text=text, reading_order_applied=True, ocr_used=False,
            processing_time_ms=(time.perf_counter() - t0) * 1000,
        )