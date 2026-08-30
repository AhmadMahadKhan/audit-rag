import asyncio
from pathlib import Path

from app.parsing.lm_parser import LMStudioVisionParser


async def main():

    image_path = Path("2.png")

    if not image_path.exists():
        print("test.png not found")
        return

    image_bytes = image_path.read_bytes()

    parser = LMStudioVisionParser()

    text = await parser.extract_text(
        image_bytes,
        page_number=1,
    )

    print("\n========== QWEN2.5-VL RESULT ==========\n")

    print(text)


if __name__ == "__main__":
    asyncio.run(main())