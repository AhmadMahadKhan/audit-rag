# ===== app/parsing/registry.py =====
from app.parsing.pdf_parser import PDFParser
from app.parsing.docx_parser import DocxParser
from app.parsing.xlsx_parser import XlsxParser
from app.parsing.pptx_parser import PptxParser
from app.parsing.html_parser import HtmlParser
from app.parsing.image_parser import ImageParser
from app.parsing.text_parser import TextParser
from app.core.exceptions import InvalidDocument

EXTENSION_MAP = {
    "pdf": PDFParser, 
    "docx": DocxParser, 
    "xlsx": XlsxParser, 
    "pptx": PptxParser,
    "html": HtmlParser, 
    "htm": HtmlParser,
    "txt": TextParser,
    "md": TextParser,
    "png": ImageParser, 
    "jpg": ImageParser, 
    "jpeg": ImageParser, 
    "tiff": ImageParser, 
    "bmp": ImageParser,
}

def get_parser(extension: str):
    parser_cls = EXTENSION_MAP.get(extension.lower())
    if not parser_cls:
        raise InvalidDocument(f"No parser registered for .{extension}")
    return parser_cls()