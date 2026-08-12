# ===== app/parsing/html_parser.py =====
import time
from bs4 import BeautifulSoup
from app.parsing.base import BaseParser
from app.parsing.schema import ParsedDocument, PageInfo, Block

class HtmlParser(BaseParser):
    name = "html_parser"
    version = "1.0"

    async def parse(self, document_id: str, content: bytes) -> ParsedDocument:
        t0 = time.perf_counter()
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        blocks, raw_text_parts = [], []
        order = 0
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
            text = el.get_text(strip=True)
            if not text:
                continue
            block_type = "heading" if el.name.startswith("h") else ("list" if el.name == "li" else "paragraph" if el.name == "p" else "table")
            blocks.append(Block(block_id=f"{document_id}_b{order}", type=block_type, text=text, page=1, order=order))
            raw_text_parts.append(text)
            order += 1

        return ParsedDocument(
            document_id=document_id, source_format="html", parser_name=self.name, parser_version=self.version,
            pages=[PageInfo(page_number=1)], blocks=blocks, tables=[], images=[],
            raw_text="\n".join(raw_text_parts), reading_order_applied=True, ocr_used=False,
            processing_time_ms=(time.perf_counter() - t0) * 1000,
        )
