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

    async def extract_from_image_bytes(self, image_bytes: bytes, page_num: int, start_order: int) -> tuple[list[Block], str]:
        image = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)

        blocks, texts = [], []
        order = start_order
        n = len(data["text"])
        i = 0
        while i < n:
            word = data["text"][i].strip()
            conf = int(data["conf"][i]) if data["conf"][i] != "-1" else -1
            if word and conf >= self.min_confidence:
                blocks.append(Block(
                    block_id=f"ocr_p{page_num}_b{order}", type="paragraph", text=word, page=page_num, order=order,
                    bbox=BoundingBox(page=page_num, x=data["left"][i], y=data["top"][i],
                                      width=data["width"][i], height=data["height"][i], confidence=conf / 100),
                    confidence=conf / 100,
                ))
                texts.append(word)
                order += 1
            i += 1
        return blocks, " ".join(texts)