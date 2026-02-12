"""Google Cloud Storage implementation"""

import json
from typing import Any

from google.cloud import storage  # type: ignore[import-untyped]
from google.oauth2 import service_account  # type: ignore[import-untyped]

from axion_server.gateways.storage.base import ObjectRef, ObjectStore


class GCSObjectStore(ObjectStore):
    """Google Cloud Storage implementation of ObjectStore"""

    def __init__(
        self,
        bucket: str,
        project_id: str | None = None,
        credentials_path: str | None = None,
    ):
        self.bucket_name = bucket
        self.project_id = project_id

        # Initialize client
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self._client = storage.Client(
                project=project_id,
                credentials=credentials,
            )
        else:
            # Use default credentials (e.g., from GCE metadata server)
            self._client = storage.Client(project=project_id)

        self._bucket = self._client.bucket(bucket)

    async def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store bytes at the given key"""
        blob = self._bucket.blob(key)

        if content_type:
            blob.content_type = content_type
        if metadata:
            blob.metadata = metadata

        # GCS client is synchronous, but we wrap it for async interface
        blob.upload_from_string(data, content_type=content_type)

        return ObjectRef(
            key=key,
            bucket=self.bucket_name,
            provider="gcs",
            size=len(data),
            content_type=content_type,
            metadata=metadata,
        )

    async def put_json(
        self,
        key: str,
        data: Any,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store JSON data at the given key"""
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return await self.put_bytes(
            key, json_bytes, content_type="application/json", metadata=metadata
        )

    async def get_bytes(self, key: str) -> bytes:
        """Retrieve bytes from the given key"""
        blob = self._bucket.blob(key)
        return blob.download_as_bytes()

    async def get_json(self, key: str) -> Any:
        """Retrieve JSON data from the given key"""
        data = await self.get_bytes(key)
        return json.loads(data.decode("utf-8"))

    async def exists(self, key: str) -> bool:
        """Check if an object exists at the given key"""
        blob = self._bucket.blob(key)
        return blob.exists()

    async def delete(self, key: str) -> bool:
        """Delete an object at the given key"""
        blob = self._bucket.blob(key)
        try:
            blob.delete()
            return True
        except Exception:
            return False

    async def list_keys(self, prefix: str) -> list[ObjectRef]:
        """List all objects with the given prefix"""
        blobs = self._client.list_blobs(self.bucket_name, prefix=prefix)
        return [
            ObjectRef(
                key=blob.name,
                bucket=self.bucket_name,
                provider="gcs",
                size=blob.size,
                content_type=blob.content_type,
                metadata=dict(blob.metadata) if blob.metadata else None,
            )
            for blob in blobs
        ]

    async def presign_get(self, key: str, expires_sec: int = 3600) -> str:
        """Generate a presigned URL for GET operations"""
        from datetime import timedelta

        blob = self._bucket.blob(key)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_sec),
            method="GET",
        )

    async def presign_put(
        self, key: str, content_type: str | None = None, expires_sec: int = 3600
    ) -> str:
        """Generate a presigned URL for PUT operations"""
        from datetime import timedelta

        blob = self._bucket.blob(key)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_sec),
            method="PUT",
            content_type=content_type,
        )
