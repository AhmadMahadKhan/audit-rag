# ===== app/parsing/image_parser.py =====
import time
from app.parsing.base import BaseParser
from app.parsing.schema import ParsedDocument, PageInfo
from app.parsing.ocr_parser import OCRParser

class ImageParser(BaseParser):
    name = "image_parser"
    version = "1.0"

    def __init__(self):
        self.ocr = OCRParser()

    async def parse(self, document_id: str, content: bytes) -> ParsedDocument:
        t0 = time.perf_counter()
        blocks, text = await self.ocr.extract_from_image_bytes(content, page_num=1, start_order=0)
        warnings = ["Low/no OCR confidence"] if not blocks else []
        return ParsedDocument(
            document_id=document_id, source_format="image", parser_name=self.name, parser_version=self.version,
            pages=[PageInfo(page_number=1, is_scanned=True)], blocks=blocks, tables=[], images=[],
            raw_text=text, reading_order_applied=False, ocr_used=True,
            processing_time_ms=(time.perf_counter() - t0) * 1000, warnings=warnings,
        )