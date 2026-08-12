# ===== app/observability/metrics.py =====
"""Prometheus metric definitions — one module so every service imports from
here rather than defining metrics ad hoc."""
from prometheus_client import Counter, Histogram, Gauge

API_REQUEST_COUNT = Counter("api_requests_total", "Total API requests", ["method", "path", "status"])
API_REQUEST_LATENCY = Histogram("api_request_duration_seconds", "API request latency", ["method", "path"])

DOCUMENT_PIPELINE_DURATION = Histogram(
    "document_pipeline_stage_duration_seconds", "Duration of each pipeline stage",
    ["stage"],  # upload|classification|parsing|ocr|metadata|entity|fact|rules|chunking|embedding|indexing
)
DOCUMENT_PIPELINE_FAILURES = Counter("document_pipeline_failures_total", "Pipeline stage failures", ["stage"])

OCR_REQUESTS = Counter("ocr_requests_total", "OCR requests", ["status"])
OCR_CONFIDENCE = Histogram("ocr_confidence_score", "OCR confidence distribution")

EMBEDDING_REQUESTS = Counter("embedding_requests_total", "Embedding requests", ["provider", "status"])
EMBEDDING_LATENCY = Histogram("embedding_generation_duration_seconds", "Embedding latency", ["provider"])

RETRIEVAL_LATENCY = Histogram("retrieval_stage_duration_seconds", "Retrieval stage latency", ["stage"])  # dense|bm25|fusion|rerank

LLM_REQUESTS = Counter("llm_requests_total", "LLM requests", ["provider", "model", "status"])
LLM_TOKENS = Counter("llm_tokens_total", "LLM tokens", ["provider", "model", "direction"])  # direction=input|output
LLM_LATENCY = Histogram("llm_generation_duration_seconds", "LLM generation latency", ["provider", "model"])
LLM_TTFT = Histogram("llm_time_to_first_token_seconds", "Time to first token", ["provider", "model"])

STREAM_COMPLETIONS = Counter("stream_completions_total", "Stream outcomes", ["status"])  # completed|cancelled|failed

QUEUE_SIZE = Gauge("queue_size", "Current queue length", ["queue_name"])
QUEUE_JOBS = Counter("queue_jobs_total", "Queue jobs processed", ["queue_name", "status"])

VECTOR_DB_LATENCY = Histogram("vector_db_operation_duration_seconds", "Qdrant op latency", ["operation"])

ERROR_COUNT = Counter("application_errors_total", "Application errors", ["category", "exception_type"])
