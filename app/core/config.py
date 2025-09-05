from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, SecretStr
from typing import Optional, List, Any
import secrets

class Settings(BaseSettings):
    """Application settings with Pydantic v2 configuration"""
    
    # API Settings
    PROJECT_NAME: str = Field(
        default="OpenFP&A API",
        description="Project name for API documentation"
    )
    VERSION: str = Field(
        default="1.0.0",
        description="API version"
    )
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API v1 route prefix"
    )
    
    # Database
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Full database URL (overrides individual settings)"
    )
    POSTGRES_USER: str = Field(
        default="openfpa_user",
        description="PostgreSQL username"
    )
    POSTGRES_PASSWORD: SecretStr = Field(
        default=SecretStr("openfpa_pass"),
        description="PostgreSQL password"
    )
    POSTGRES_DB: str = Field(
        default="openfpa",
        description="PostgreSQL database name"
    )
    POSTGRES_HOST: str = Field(
        default="localhost",
        description="PostgreSQL host"
    )
    POSTGRES_PORT: str = Field(
        default="5432",
        description="PostgreSQL port"
    )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    # Security
    SECRET_KEY: SecretStr = Field(
        default=SecretStr(secrets.token_urlsafe(32)),
        description="Secret key for JWT encoding"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration in minutes"
    )
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
        validate_default=True,  # Validate default values
        json_schema_extra={
            "example": {
                "PROJECT_NAME": "OpenFP&A API",
                "DATABASE_URL": "postgresql://user:pass@localhost:5432/dbname",
                "SECRET_KEY": "your-secret-key-here"
            }
        }
    )
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    @property
    def get_database_url(self) -> str:
        """Get database URL, either from DATABASE_URL or constructed from individual settings"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Use get_secret_value() for SecretStr
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return f"postgresql://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()