"""Central configuration. Everything is env-overridable; nothing is hardcoded secret."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Settings:
    # --- Database -------------------------------------------------------
    # Default SQLite so the project runs with zero setup.
    # Set DATABASE_URL to a postgresql+psycopg2://... string to use Postgres.
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'opspilot.db'}")

    # --- Ollama (local only, no paid APIs) ------------------------------
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "90"))

    # --- RAG ------------------------------------------------------------
    # 'tfidf' = pure sklearn, zero downloads, always works.
    # 'ollama' = local embedding model via Ollama (nomic-embed-text).
    EMBEDDING_MODE: str = os.getenv("EMBEDDING_MODE", "tfidf")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "80"))

    # --- Auth -----------------------------------------------------------
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-change-me")
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))

    # --- SQL tool guardrails --------------------------------------------
    SQL_ROW_LIMIT: int = int(os.getenv("SQL_ROW_LIMIT", "200"))
    SQL_TIMEOUT_S: int = int(os.getenv("SQL_TIMEOUT_S", "10"))

    # --- Paths ----------------------------------------------------------
    RAW_DIR: Path = ROOT / "data" / "raw"
    DOC_DIR: Path = ROOT / "data" / "documents"
    PROC_DIR: Path = ROOT / "data" / "processed"

    BILLING_MONTH: str = os.getenv("BILLING_MONTH", "2026-09")


settings = Settings()
