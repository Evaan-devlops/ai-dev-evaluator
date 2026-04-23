from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/rag_service"
    VECTOR_DIMENSION: int = 1536

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_ACCESS_TOKEN: str = ""

    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_ACCESS_TOKEN: str = ""

    OCR_PROVIDER: str = ""
    OCR_ACCESS_TOKEN: str = ""

    MAX_AGENT_STEPS: int = 6
    MAX_CONTEXT_TOKENS: int = 8000
    DEFAULT_TOP_K: int = 8
    LOG_LEVEL: str = "INFO"

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50


settings = Settings()
