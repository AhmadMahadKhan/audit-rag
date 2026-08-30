

import base64
import io
import time

from PIL import Image

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging_config import logger


class LMStudioVisionParser:
    """
    Vision-based document/image extraction using Qwen2.5-VL
    through LM Studio.
    """

    def __init__(
        self,
        model: str | None = None,
    ):
        self.model = model or settings.LMSTUDIO_VISION_MODEL

        self.client = AsyncOpenAI(
            base_url=settings.LMSTUDIO_URL,
            api_key=settings.LMSTUDIO_API_KEY,
            timeout=settings.LMSTUDIO_TIMEOUT,
        )

    # ============================================================
    # IMAGE PREPARATION
    # ============================================================

    def _prepare_image(self, image_bytes: bytes) -> str:
        """
        Convert image bytes into a base64 data URL.

        Large images are resized before being sent to the
        vision model to reduce memory usage and latency.
        """

        image = Image.open(io.BytesIO(image_bytes))

        # Convert formats such as RGBA/P to RGB.
        if image.mode != "RGB":
            image = image.convert("RGB")

        max_size = settings.LMSTUDIO_MAX_IMAGE_SIZE

        if max(image.width, image.height) > max_size:
            image.thumbnail(
                (max_size, max_size),
                Image.Resampling.LANCZOS,
            )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=90,
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return f"data:image/jpeg;base64,{encoded}"

    # ============================================================
    # IMAGE → TEXT
    # ============================================================

    async def extract_text(
        self,
        image_bytes: bytes,
        page_number: int | None = None,
    ) -> str:
        """
        Send an image to Qwen2.5-VL and extract its contents.

        The model is instructed to preserve:

        - headings
        - paragraphs
        - tables
        - numbers
        - dates
        - monetary values
        - labels
        - document structure
        """

        t0 = time.perf_counter()

        try:
            image_data_url = self._prepare_image(image_bytes)

            prompt = """
You are a document understanding and OCR engine.

Extract ALL readable information from this image.

Important rules:

1. Preserve the original meaning and wording.
2. Do NOT summarize.
3. Do NOT invent missing text.
4. Preserve numbers exactly.
5. Preserve monetary values exactly.
6. Preserve dates exactly.
7. Preserve table contents.
8. Preserve headings.
9. Preserve line items.
10. Preserve IDs, invoice numbers, account numbers and reference numbers.
11. If there is a table, represent it in a readable row/column format.
12. If text is unclear, mark it as [UNCLEAR] instead of guessing.
13. Return ONLY the extracted document content.
14. Do not add explanations about the image.

This output will be used by a downstream document intelligence
and RAG system, so accuracy is more important than brevity.
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Extract the complete contents "
                                    f"of page {page_number}."
                                    if page_number
                                    else
                                    "Extract the complete contents "
                                    "of this image."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url,
                                },
                            },
                        ],
                    },
                ],
                temperature=0,
            )

            text = response.choices[0].message.content or ""

            text = text.strip()

            elapsed = (time.perf_counter() - t0) * 1000

            logger.info(
                "lmstudio_vision_extraction_completed",
                model=self.model,
                page=page_number,
                chars=len(text),
                processing_time_ms=round(elapsed, 2),
            )

            return text

        except Exception as exc:
            logger.error(
                "lmstudio_vision_extraction_failed",
                model=self.model,
                page=page_number,
                error=str(exc),
            )

            return ""