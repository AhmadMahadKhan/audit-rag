"""
PDF Parser
==========

Processing strategy per page:

                    PDF page
                       |
                       v
                 PyMuPDF text
                       |
             +---------+---------+
             |                   |
        enough text          little text
             |                   |
             v                   v
        normal text          render page
                                 |
                                 v
                            Tesseract OCR
                                 |
                         +-------+-------+
                         |               |
                    good confidence   low confidence
                         |               |
                         v               v
                    use OCR          Qwen2.5-VL
                                         |
                                    if failure
                                         |
                                         v
                                  Tesseract fallback

This allows a PDF to contain both digital and scanned pages.
"""

import time

import fitz

from app.parsing.base import BaseParser

from app.parsing.schema import (
    ParsedDocument,
    PageInfo,
    Block,
    BoundingBox,
    ParsedImage,
)

from app.parsing.ocr_parser import OCRParser
from app.parsing.lm_parser import LMStudioVisionParser
from app.parsing.schema import ParsedTable, TableCell


from app.core.config import settings


# Number of characters below which a page is considered
# potentially scanned.
SCANNED_TEXT_THRESHOLD = 20


class PDFParser(BaseParser):

    name = "pdf_parser"
    version = "2.0"

    def __init__(self):

        self.ocr = OCRParser()

        self.vision = LMStudioVisionParser()

    async def parse(
        self,
        document_id: str,
        content: bytes,
    ) -> ParsedDocument:

        t0 = time.perf_counter()

        doc = fitz.open(
            stream=content,
            filetype="pdf",
        )

        pages = []
        blocks = []
        images = []
        tables = []
        raw_text_parts = []
        warnings = []

        order = 0

        ocr_used = False

        # ========================================================
        # PROCESS EVERY PAGE
        # ========================================================

        for page_num, page in enumerate(
            doc,
            start=1,
        ):

            text = page.get_text("text")

            text_clean = text.strip()

            is_scanned = (
                len(text_clean)
                < SCANNED_TEXT_THRESHOLD
            )

            pages.append(
                PageInfo(
                    page_number=page_num,
                    width=page.rect.width,
                    height=page.rect.height,
                    is_scanned=is_scanned,
                )
            )

            # ====================================================
            # CASE 1
            # NORMAL DIGITAL PAGE
            # ====================================================

            if not is_scanned:

                for block in page.get_text(
                    "blocks"
                ):

                    x0, y0, x1, y1, block_text, *_ = block

                    block_text = block_text.strip()

                    if not block_text:
                        continue

                    blocks.append(
                        Block(
                            block_id=(
                                f"{document_id}"
                                f"_p{page_num}"
                                f"_b{order}"
                            ),
                            type="paragraph",
                            text=block_text,
                            page=page_num,
                            order=order,
                            bbox=BoundingBox(
                                page=page_num,
                                x=x0,
                                y=y0,
                                width=x1 - x0,
                                height=y1 - y0,
                            ),
                        )
                    )
                    order +=1 
                raw_text_parts.append(text)
                try: 
                    found_tables = page.find_tables()
                except Exception as exc : 
                    found_tables = []
                    warnings.append(
                        f"page {page_num}: table detection failed ({exc})"
                    )
                for tbl in found_tables:
                    try:
                        extracted = tbl.extract()  # list[list[str]]
                    except Exception:
                        continue

                    if not extracted or not any(any(row) for row in extracted):
                        continue

                    cells = []
                    for r_idx, row in enumerate(extracted):
                        for c_idx, cell_text in enumerate(row):
                            cells.append(
                                TableCell(
                                    row=r_idx,
                                    col=c_idx,
                                    text=(cell_text or "").strip(),
                                )
                            )

                    x0, y0, x1, y1 = tbl.bbox

                    tables.append(
                        ParsedTable(
                            table_id=f"{document_id}_p{page_num}_t{order}",
                            page=page_num,
                            order=order,
                            cells=cells,
                            bbox=BoundingBox(
                                page=page_num, x=x0, y=y0,
                                width=x1 - x0, height=y1 - y0,
                            ),
                        )
                    )


                    order += 1
                else : 
                    ocr_used = True
                    warnings.append(f"Page {page_num}: scanned page — table extraction not supported for OCR/vision fallback")
                    

                

            # ====================================================
            # CASE 2
            # SCANNED / LOW TEXT PAGE
            # ====================================================

            else:

                ocr_used = True

                # -----------------------------------------------
                # Render PDF page to image
                # -----------------------------------------------

                pix = page.get_pixmap(
                    dpi=200,
                    alpha=False,
                )

                img_bytes = pix.tobytes(
                    "png"
                )

                # -----------------------------------------------
                # Tesseract
                # -----------------------------------------------

                (
                    ocr_blocks,
                    ocr_text,
                    ocr_confidence,
                ) = await self.ocr.extract_from_image_bytes(
                    img_bytes,
                    page_num=page_num,
                    start_order=order,
                )

                threshold = settings.OCR_MIN_CONFIDENCE

                # -----------------------------------------------
                # GOOD OCR
                # -----------------------------------------------

                if (
                    ocr_confidence >= threshold
                    and ocr_text.strip()
                ):

                    blocks.extend(
                        ocr_blocks
                    )

                    order += len(
                        ocr_blocks
                    )

                    raw_text_parts.append(
                        ocr_text
                    )

                # -----------------------------------------------
                # BAD OCR → QWEN2.5-VL
                # -----------------------------------------------

                else:

                    vision_text = (
                        await self.vision.extract_text(
                            img_bytes,
                            page_number=page_num,
                        )
                    )

                    if vision_text.strip():

                        vision_block = Block(
                            block_id=(
                                f"{document_id}"
                                f"_p{page_num}"
                                f"_vision_b{order}"
                            ),
                            type="paragraph",
                            text=vision_text,
                            page=page_num,
                            order=order,
                        )

                        blocks.append(
                            vision_block
                        )

                        order += 1

                        raw_text_parts.append(
                            vision_text
                        )

                        warnings.append(
                            (
                                f"Page {page_num}: "
                                f"Tesseract confidence "
                                f"{ocr_confidence:.1f}% "
                                f"< {threshold}%; "
                                "Qwen2.5-VL used."
                            )
                        )

                    # -------------------------------------------
                    # QWEN FAILED → TESSERACT FALLBACK
                    # -------------------------------------------

                    else:

                        blocks.extend(
                            ocr_blocks
                        )

                        order += len(
                            ocr_blocks
                        )

                        raw_text_parts.append(
                            ocr_text
                        )

                        warnings.append(
                            (
                                f"Page {page_num}: "
                                f"Tesseract confidence "
                                f"{ocr_confidence:.1f}% "
                                f"< {threshold}%; "
                                "Qwen2.5-VL failed; "
                                "Tesseract result retained."
                            )
                        )

            # ====================================================
            # EXTRACT EMBEDDED IMAGES
            # ====================================================

            for img_idx, img in enumerate(
                page.get_images(
                    full=True
                )
            ):

                images.append(
                    ParsedImage(
                        image_id=(
                            f"{document_id}"
                            f"_p{page_num}"
                            f"_img{img_idx}"
                        ),
                        page=page_num,
                    )
                )

        doc.close()

        # ========================================================
        # FINAL DOCUMENT
        # ========================================================

        return ParsedDocument(
            document_id=document_id,
            source_format="pdf",
            parser_name=self.name,
            parser_version=self.version,
            pages=pages,
            blocks=blocks,
            tables = tables,
            images=images,
            raw_text="\n".join(
                raw_text_parts
            ),
            reading_order_applied=True,
            ocr_used=ocr_used,
            processing_time_ms=(
                time.perf_counter() - t0
            ) * 1000,
            warnings=warnings,
        )