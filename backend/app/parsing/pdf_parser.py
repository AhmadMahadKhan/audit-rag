# ===== app/parsing/pdf_parser.py =====
import time
import fitz  # PyMuPDF
from app.parsing.base import BaseParser
from app.parsing.schema import ParsedDocument, PageInfo, Block, BoundingBox, ParsedImage
from app.parsing.ocr_parser import OCRParser

SCANNED_TEXT_THRESHOLD = 20  # chars/page below this triggers OCR

class PDFParser(BaseParser):
    name = "pdf_parser"
    version = "1.0"

    def __init__(self):
        self.ocr = OCRParser()

    async def parse(self, document_id: str, content: bytes) -> ParsedDocument:
        t0 = time.perf_counter()
        doc = fitz.open(stream=content, filetype="pdf")
        pages, blocks, images = [], [], []
        raw_text_parts, warnings = [], []
        order = 0
        ocr_used = False

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            is_scanned = len(text.strip()) < SCANNED_TEXT_THRESHOLD
            pages.append(PageInfo(page_number=page_num, width=page.rect.width, height=page.rect.height, is_scanned=is_scanned))

            if is_scanned:
                ocr_used = True
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                ocr_blocks, ocr_text = await self.ocr.extract_from_image_bytes(img_bytes, page_num, order)
                blocks.extend(ocr_blocks)
                order += len(ocr_blocks)
                raw_text_parts.append(ocr_text)
                if not ocr_blocks:
                    warnings.append(f"Low/no OCR confidence on page {page_num}")
            else:
                for b in page.get_text("blocks"):
                    x0, y0, x1, y1, block_text, *_ = b
                    if not block_text.strip():
                        continue
                    blocks.append(Block(
                        block_id=f"{document_id}_p{page_num}_b{order}", type="paragraph",
                        text=block_text.strip(), page=page_num, order=order,
                        bbox=BoundingBox(page=page_num, x=x0, y=y0, width=x1 - x0, height=y1 - y0),
                    ))
                    order += 1
                raw_text_parts.append(text)

            for img_idx, img in enumerate(page.get_images(full=True)):
                images.append(ParsedImage(image_id=f"{document_id}_p{page_num}_img{img_idx}", page=page_num))

        doc.close()
        return ParsedDocument(
            document_id=document_id, source_format="pdf", parser_name=self.name, parser_version=self.version,
            pages=pages, blocks=blocks, tables=[], images=images, raw_text="\n".join(raw_text_parts),
            reading_order_applied=True, ocr_used=ocr_used,
            processing_time_ms=(time.perf_counter() - t0) * 1000, warnings=warnings,
        )