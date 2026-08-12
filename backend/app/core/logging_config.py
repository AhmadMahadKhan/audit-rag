
# ===== app/core/logging_config.py 
import logging
import sys
import structlog
from app.observability.redaction import redact_dict

def redaction_processor(logger, method_name, event_dict):
    return redact_dict(event_dict)

logging.basicConfig(level=logging.INFO, format="%(message)s",
                     handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("logs/app.log")])

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        redaction_processor,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()