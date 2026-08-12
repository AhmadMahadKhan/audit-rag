# ===== app/core/exceptions.py =====

class ApplicationError(Exception):
    """Base class for all application-raised errors."""
    error_code: str = "application_error"
    status_code: int = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DocumentNotFound(ApplicationError):
    error_code = "document_not_found"
    status_code = 404


class InvalidDocument(ApplicationError):
    error_code = "invalid_document"
    status_code = 422


class DuplicateDocument(ApplicationError):
    error_code = "duplicate_document"
    status_code = 409


class StorageError(ApplicationError):
    error_code = "storage_error"
    status_code = 500


class OCRFailed(ApplicationError):
    error_code = "ocr_failed"
    status_code = 500


class RuleEngineError(ApplicationError):
    error_code = "rule_engine_error"
    status_code = 500


class AuthenticationError(ApplicationError):
    error_code = "authentication_error"
    status_code = 401


class AuthorizationError(ApplicationError):
    error_code = "authorization_error"
    status_code = 403


class ValidationFailed(ApplicationError):
    error_code = "validation_failed"
    status_code = 422