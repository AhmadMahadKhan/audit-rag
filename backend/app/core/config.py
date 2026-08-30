# ===== app/core/config.py =====
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "audit-rag"
    ENVIROMENT: str = "development"
    # ENVIROMENT : str = ""
    database_url: str ="sqlite+aiosqlite:///./app.db"
    debug: bool = True
    log_level: str = "INFO"
    SECRET_KEY: str = "change-me-in-prod"

    # classification
    CLASSIFICATION_MODEL : str = "qwen2.5:latest"
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.6
    CLASSIFICATION_METHOD: str = "ai_based"  # rule_based | ai_based | hybrid   
    
    # authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    # storage
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_PATH: str = "./storage"
    ALLOWED_EXTENSIONS: str = "pdf,docx,xlsx,pptx,csv,html,txt,md,png,jpg,jpeg,tiff,bmp,eml,md"
    MAX_UPLOAD_SIZE_MB: int = 50
    DUPLICATE_POLICY: str = "reject"  # reject | replace | version | keep_both


    # ocr 
    OCR_MIN_CONFIDENCE: int = 40
    OCR_PROVIDER: str = "tesseract"
    OCR_LANGUAGE : str = 'eng'

    # embedding
    EMBEDDING_PROVIDER: str = "ollama"
    EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    EMBEDDING_DIMENSION: int = 768
    EMBEDDING_BATCH_SIZE: int = 16
    QDRANT_URL: str = "http://127.0.0.1:6333"
    QDRANT_API_KEY: str | None = None

    # re-ranking
    RERANKER_PROVIDER: str = "sentence_transformers"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K_IN: int = 50
    RERANK_TOP_N_OUT: int = 5
    RERANK_MIN_SCORE: float = 0.0
    RERANK_DIVERSITY_THRESHOLD: float = 0.92  # cosine sim above this = near-duplicate

    # llm 
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "qwen2.5:latest"
    LLM_MAX_CONTEXT_TOKENS: int = 10000
    LLM_RESPONSE_RESERVE_TOKENS: int = 800
    CHAT_CONFIDENCE_THRESHOLD: float = 0.4

    # risk
    RISK_THRESHOLD_MEDIUM: float = 25.0
    RISK_THRESHOLD_HIGH: float = 60.0
    RISK_THRESHOLD_CRITICAL: float = 85.0
    APPROVAL_LIMIT_DEFAULT: float = 10000.0

    #OBSVERABLITY
    OTEL_EXPORTER_ENDPOINT: str | None = None  # e.g. http://otel-collector:4317
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # COSTING
    LLM_INPUT_COST_PER_1K: float = 0.0  # 0 for local Ollama; set for cloud providers
    LLM_OUTPUT_COST_PER_1K: float = 0.0
    EMBEDDING_COST_PER_1K: float = 0.0

    # OLLAMA
    OLLAMA_URL: str = "http://127.0.0.1:11434"
    OLLAMA_API_KEY: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"
    # OPENAI
    OPENAI_API_KEY: str | None = None

    # LM STOUDIO    
    LMSTUDIO_URL: str = "http://127.0.0.1:1234/v1"
    LMSTUDIO_API_KEY: str = "lm-studio"
    LMSTUDIO_TIMEOUT: float = 120.0
    LMSTUDIO_MAX_IMAGE_SIZE: int = 1600
    LMSTUDIO_VISION_MODEL: str = "qwen2.5-vl-7b-instruct"

    # audit agent 
    AUDIT_MODEL: str = "llama3.1"
    AUDIT_MEMORY_TOKEN_LIMIT: int = 2000  # trigger compaction above this
    AUDIT_MAX_FINDINGS_KEPT: int = 40   
    
    
    class Config:
        env_file = (".env", "../.env")
        extra = "ignore"

settings = Settings()