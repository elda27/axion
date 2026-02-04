"""Application configuration using Pydantic Settings"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Axion"
    debug: bool = False

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://axion:axion_dev_password@localhost:5433/axion",
        description="Database connection URL",
    )
    database_type: Literal["postgresql", "sqlite"] = "postgresql"

    # Object Storage
    object_store_provider: Literal["s3", "minio", "local"] = "minio"
    object_store_endpoint: str = "http://localhost:9010"
    object_store_access_key: str = "minioadmin"
    object_store_secret_key: str = "minioadmin"
    object_store_bucket: str = "axion-artifacts"
    object_store_region: str = "us-east-1"
    object_store_local_path: str = "./data/object_store"

    # API
    api_prefix: str = "/v1"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
