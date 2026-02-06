"""Object store factory"""

from functools import lru_cache

from axion.config import get_settings
from axion_server.storage.base import ObjectStore
from axion_server.storage.local import LocalObjectStore
from axion_server.storage.s3 import S3ObjectStore


@lru_cache
def get_object_store() -> ObjectStore:
    """Get object store instance based on configuration"""
    settings = get_settings()

    if settings.object_store_provider == "local":
        return LocalObjectStore(
            base_path=settings.object_store_local_path,
            bucket=settings.object_store_bucket,
        )
    else:
        # S3 or MinIO
        return S3ObjectStore(
            bucket=settings.object_store_bucket,
            endpoint_url=(
                settings.object_store_endpoint
                if settings.object_store_provider == "minio"
                else None
            ),
            access_key=settings.object_store_access_key,
            secret_key=settings.object_store_secret_key,
            region=settings.object_store_region,
        )
