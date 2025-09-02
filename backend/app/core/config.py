import os
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "FP&A Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-secret-key-change-this-in-production"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://fpa_user:fpa_password@localhost:5432/fpa_db"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Data Processing
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    PANDAS_CHUNK_SIZE: int = 10000

    # Supported Data Sources
    SUPPORTED_DB_TYPES: List[str] = ["postgresql", "mysql", "mssql", "oracle", "sqlite"]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
