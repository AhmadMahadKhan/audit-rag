# ===== app/schemas/parsing.py =====
from pydantic import BaseModel
from datetime import datetime

class ParsingResultOut(BaseModel):
    id: str
    document_id: str
    parser_name: str
    ocr_used: bool
    status: str
    error_message: str | None
    processing_time_ms: float | None
    created_at: datetime

    class Config:
        from_attributes = True

class ParsingDetailOut(ParsingResultOut):
    raw_text: str | None
    parsed_json: dict