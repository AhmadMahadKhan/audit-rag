# ===== app/parsing/ocr_parser.py =====
"""OCR provider abstraction. Default: pytesseract (simplest to run locally without GPU).
Swap to PaddleOCR by implementing the same interface if higher accuracy is needed."""
import io
from PIL import Image
import pytesseract
from app.parsing.schema import Block, BoundingBox
from app.core.config import settings

class OCRParser:
    def __init__(self, lang: str = "eng"):
        self.lang = lang
        self.min_confidence = getattr(settings, "OCR_MIN_CONFIDENCE", 40)

    
    async def extract_from_image_bytes(
        self,
        image_bytes: bytes,
        page_num: int,
        start_order: int = 0,
    ) -> tuple[list[Block], str, float]:

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        image = image.convert("RGB")

        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=pytesseract.Output.DICT,
        )

        blocks = []
        texts = []

        confidences = []

        order = start_order

        n = len(data["text"])

        for i in range(n):

            word = data["text"][i].strip()

            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1

            if not word:
                continue

            if conf < 0:
                continue

            confidences.append(conf)

            
            
            # The FINAL decision whether Tesseract is good enough
            # is made using the average confidence.
            if conf >= 10:

                blocks.append(
                    Block(
                        block_id=(
                            f"ocr_p{page_num}_b{order}"
                        ),
                        type="paragraph",
                        text=word,
                        page=page_num,
                        order=order,
                        bbox=BoundingBox(
                            page=page_num,
                            x=data["left"][i],
                            y=data["top"][i],
                            width=data["width"][i],
                            height=data["height"][i],
                            confidence=conf / 100,
                        ),
                        confidence=conf / 100,
                    )
                )

                texts.append(word)

                order += 1

        if confidences:
            average_confidence = (
                sum(confidences) /
                len(confidences)
            )
        else:
            average_confidence = 0.0

        extracted_text = " ".join(texts)

        return (
            blocks,
            extracted_text,
            average_confidence,
        )