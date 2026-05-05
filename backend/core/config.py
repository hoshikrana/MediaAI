import os
from pathlib import Path
from typing import Literal
from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Core application settings populated from environment variables."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # === Application ===
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    SECRET_KEY: str
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # === Database ===
    DATABASE_URL: str = "sqlite+aiosqlite:///./medsight.db"

    # === JWT ===
    JWT_SECRET_KEY: str
    JWT_SECRET_KEY_OLD: str | None = None  # Used for key rotation
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # === Google OAuth ===
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # === HuggingFace ===
    HF_TOKEN: str = ""

    # === ML Config ===
    MODEL_CACHE_DIR: Path = Path("C:/hf_cache")
    TEMP_DIR: Path = Path("./backend/temp")
    MAX_UPLOAD_SIZE_MB: int = 10
    GPU_VRAM_BUDGET_MB: int = 3500

    # === Rate Limiting ===
    RATE_LIMIT_ANALYZE: str = "10/hour"
    RATE_LIMIT_CHAT: str = "50/hour"
    RATE_LIMIT_AUTH: str = "5/minute"

    # === Logging ===
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: Path = Path("./backend/logs")

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @computed_field
    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def __repr__(self) -> str:
        # NEVER show secrets in repr to prevent accidental logging
        return f"Settings(environment={self.ENVIRONMENT}, debug={self.DEBUG}, version={self.VERSION})"

# Singleton — import this everywhere
settings = Settings()

def startup_validation():
    """Validates critical infrastructure at startup."""
    errors = []
    
    try:
        settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
        settings.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        errors.append("Lack permissions to create required directories (temp, logs, cache).")

    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is not set.")

    if settings.is_production:
        if not settings.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID is required in production.")
        if settings.DEBUG:
            errors.append("DEBUG mode must be False in production.")

    if errors:
        raise RuntimeError("Startup Validation Failed:\n" + "\n".join(errors))
