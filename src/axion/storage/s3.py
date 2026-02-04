"""S3/MinIO object storage implementation"""

import json
from contextlib import asynccontextmanager
from typing import Any

import aioboto3

from axion.storage.base import ObjectRef, ObjectStore


class S3ObjectStore(ObjectStore):
    """S3/MinIO implementation of ObjectStore"""

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = "us-east-1",
    ):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self._session = aioboto3.Session()

    @asynccontextmanager
    async def _get_client(self):
        """Get S3 client as context manager"""
        async with self._session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        ) as client:
            yield client

    async def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store bytes at the given key"""
        extra_args: dict[str, Any] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata

        async with self._get_client() as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                **extra_args,
            )

        provider = "minio" if self.endpoint_url else "s3"
        return ObjectRef(
            key=key,
            bucket=self.bucket,
            provider=provider,
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
        async with self._get_client() as client:
            response = await client.get_object(Bucket=self.bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def get_json(self, key: str) -> Any:
        """Retrieve JSON data from the given key"""
        data = await self.get_bytes(key)
        return json.loads(data.decode("utf-8"))

    async def exists(self, key: str) -> bool:
        """Check if an object exists at the given key"""
        try:
            async with self._get_client() as client:
                await client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def list_keys(self, prefix: str) -> list[ObjectRef]:
        """List objects with the given prefix"""
        results: list[ObjectRef] = []
        provider = "minio" if self.endpoint_url else "s3"

        async with self._get_client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    results.append(
                        ObjectRef(
                            key=obj["Key"],
                            bucket=self.bucket,
                            provider=provider,
                            size=obj.get("Size"),
                        )
                    )

        return results

    async def delete(self, key: str) -> bool:
        """Delete the object at the given key"""
        try:
            async with self._get_client() as client:
                await client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def presign_get(self, key: str, expires_sec: int = 3600) -> str:
        """Generate a presigned URL for GET operations"""
        async with self._get_client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_sec,
            )
        return url

    async def presign_put(
        self, key: str, content_type: str | None = None, expires_sec: int = 3600
    ) -> str:
        """Generate a presigned URL for PUT operations"""
        params: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type

        async with self._get_client() as client:
            url = await client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=expires_sec,
            )
        return url
