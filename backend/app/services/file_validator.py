# ===== app/services/file_validator.py =====
import os
import mimetypes
from app.core.config import settings
from app.core.exceptions import InvalidDocument

DANGEROUS_EXTENSIONS = {"exe", "bat", "sh", "cmd", "msi", "dll", "js", "vbs", "ps1"}

class FileValidator:
    def __init__(self):
        self.allowed = set(settings.ALLOWED_EXTENSIONS.split(","))
        self.max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def sanitize_filename(self, filename: str) -> str:
        name = os.path.basename(filename)  # strips path traversal (../, /)
        name = name.replace("\x00", "")
        if not name or name in (".", ".."):
            raise InvalidDocument("Invalid filename")
        return name

    def validate(self, filename: str, content: bytes) -> str:
        safe_name = self.sanitize_filename(filename)
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""

        if ext in DANGEROUS_EXTENSIONS:
            raise InvalidDocument(f"File type not permitted: .{ext}")
        if ext not in self.allowed:
            raise InvalidDocument(f"Unsupported file type: .{ext}")
        if len(content) == 0:
            raise InvalidDocument("Empty file")
        if len(content) > self.max_bytes:
            raise InvalidDocument(f"File exceeds max size of {settings.MAX_UPLOAD_SIZE_MB}MB")

        mime_type, _ = mimetypes.guess_type(safe_name)
        return mime_type or "application/octet-stream"
