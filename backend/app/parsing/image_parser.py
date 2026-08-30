
"""
Image Parser
============

Processing strategy:

1. Run Tesseract first.
2. Calculate OCR confidence.
3. If confidence is above OCR_MIN_CONFIDENCE:
       use Tesseract.
4. If confidence is below threshold:
       send the image to Qwen2.5-VL through LM Studio.
5. If Qwen-VL fails:
       fall back to Tesseract result.

This gives us a cheap OCR-first strategy while still
handling difficult documents using a vision model.
"""

import time

from app.parsing.base import BaseParser
from app.parsing.schema import (
    ParsedDocument,
    PageInfo,
    Block,
)

from app.parsing.ocr_parser import OCRParser
from app.parsing.lm_parser import LMStudioVisionParser

from app.core.config import settings


class ImageParser(BaseParser):

    name = "image_parser"
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

        # ========================================================
        # STEP 1
        # TESSERACT OCR
        # ========================================================

        (
            ocr_blocks,
            ocr_text,
            ocr_confidence,
        ) = await self.ocr.extract_from_image_bytes(
            content,
            page_num=1,
            start_order=0,
        )

        threshold = settings.OCR_MIN_CONFIDENCE

        # ========================================================
        # STEP 2
        # GOOD OCR
        # ========================================================

        if (
            ocr_confidence >= threshold
            and ocr_text.strip()
        ):

            return ParsedDocument(
                document_id=document_id,
                source_format="image",
                parser_name=self.name,
                parser_version=self.version,
                pages=[
                    PageInfo(
                        page_number=1,
                        is_scanned=True,
                    )
                ],
                blocks=ocr_blocks,
                tables=[],
                images=[],
                raw_text=ocr_text,
                reading_order_applied=False,
                ocr_used=True,
                processing_time_ms=(
                    time.perf_counter() - t0
                ) * 1000,
                warnings=[],
            )

        # ========================================================
        # STEP 3
        # TESSERACT BAD → QWEN2.5-VL
        # ========================================================

        vision_text = await self.vision.extract_text(
            content,
            page_number=1,
        )

        # ========================================================
        # STEP 4
        # QWEN SUCCESS
        # ========================================================

        if vision_text.strip():

            vision_block = Block(
                block_id=f"{document_id}_vision_p1_b0",
                type="paragraph",
                text=vision_text,
                page=1,
                order=0,
            )

            return ParsedDocument(
                document_id=document_id,
                source_format="image",
                parser_name=self.name,
                parser_version=self.version,
                pages=[
                    PageInfo(
                        page_number=1,
                        is_scanned=True,
                    )
                ],
                blocks=[vision_block],
                tables=[],
                images=[],
                raw_text=vision_text,
                reading_order_applied=True,
                ocr_used=True,
                processing_time_ms=(
                    time.perf_counter() - t0
                ) * 1000,
                warnings=[
                    (
                        "Tesseract OCR confidence "
                        f"{ocr_confidence:.1f}% was below "
                        f"threshold {threshold}%; "
                        "Qwen2.5-VL used."
                    )
                ],
            )

        # ========================================================
        # STEP 5
        # QWEN FAILED → TESSERACT FALLBACK
        # ========================================================

        return ParsedDocument(
            document_id=document_id,
            source_format="image",
            parser_name=self.name,
            parser_version=self.version,
            pages=[
                PageInfo(
                    page_number=1,
                    is_scanned=True,
                )
            ],
            blocks=ocr_blocks,
            tables=[],
            images=[],
            raw_text=ocr_text,
            reading_order_applied=False,
            ocr_used=True,
            processing_time_ms=(
                time.perf_counter() - t0
            ) * 1000,
            warnings=[
                (
                    "Tesseract OCR confidence "
                    f"{ocr_confidence:.1f}% was below "
                    f"threshold {threshold}%, "
                    "Qwen2.5-VL was attempted but "
                    "returned no usable result."
                )
            ],
        )