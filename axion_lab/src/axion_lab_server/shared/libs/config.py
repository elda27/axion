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
    app_name: str = "axion-lab"
    debug: bool = False

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://axion_lab:axion_lab_dev_password@localhost:5433/axion_lab",
        description="Database connection URL",
    )
    database_type: Literal["postgresql", "sqlite"] = "postgresql"

    # Object Storage
    object_store_provider: Literal["s3", "minio", "rustfs", "gcs", "local"] = "minio"
    object_store_endpoint: str = "http://localhost:9010"
    object_store_access_key: str = "minioadmin"
    object_store_secret_key: str = "minioadmin"
    object_store_bucket: str = "axion-lab-artifacts"
    object_store_region: str = "us-east-1"
    object_store_local_path: str = "./data/object_store"

    # GCS specific settings
    gcs_project_id: str | None = None
    gcs_credentials_path: str | None = None

    # API
    api_prefix: str = "/v1"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
