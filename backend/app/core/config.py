"""
Application configuration.

Reads settings from environment variables (see .env.example).
Kept intentionally small for Phase 1 — later phases will add settings
for the LLM provider, embedding model, FAISS index path, etc.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str = "sqlite:///./data/app.db"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50
    vector_store_dir: str = "./data/vector_store"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    retrieval_top_k_default: int = 5
    retrieval_top_k_max: int = 10
    retrieval_relevance_threshold: float = 0.2
    retrieval_max_query_length: int = 500

    # LLM provider (Phase 8)
    gemini_api_key: str = ""  # optional — LLM features use template fallback if empty

    # IPO Search (live search feature)
    ipo_search_cache_ttl_hours: int = 6
    ipo_search_request_timeout: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
