"""Local filesystem object storage implementation"""

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from axion_lab_server.gateways.storage.base import ObjectRef, ObjectStore


class LocalObjectStore(ObjectStore):
    """Local filesystem implementation of ObjectStore"""

    def __init__(self, base_path: str, bucket: str = "local"):
        self.base_path = Path(base_path)
        self.bucket = bucket
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get full filesystem path for a key"""
        return self.base_path / key

    async def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store bytes at the given key"""
        path = self._get_full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

        # Store metadata in a sidecar file
        if metadata or content_type:
            meta = metadata or {}
            if content_type:
                meta["_content_type"] = content_type
            meta_path = Path(str(path) + ".meta")
            meta_path.write_text(json.dumps(meta))

        return ObjectRef(
            key=key,
            bucket=self.bucket,
            provider="local",
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
        path = self._get_full_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Object not found: {key}")
        return path.read_bytes()

    async def get_json(self, key: str) -> Any:
        """Retrieve JSON data from the given key"""
        data = await self.get_bytes(key)
        return json.loads(data.decode("utf-8"))

    async def exists(self, key: str) -> bool:
        """Check if an object exists at the given key"""
        return self._get_full_path(key).exists()

    async def list_keys(self, prefix: str) -> list[ObjectRef]:
        """List objects with the given prefix"""
        prefix_path = self._get_full_path(prefix)
        results: list[ObjectRef] = []

        if prefix_path.is_dir():
            for path in prefix_path.rglob("*"):
                if path.is_file() and not path.name.endswith(".meta"):
                    rel_key = str(path.relative_to(self.base_path)).replace("\\", "/")
                    results.append(
                        ObjectRef(
                            key=rel_key,
                            bucket=self.bucket,
                            provider="local",
                            size=path.stat().st_size,
                        )
                    )
        elif prefix_path.exists():
            results.append(
                ObjectRef(
                    key=prefix,
                    bucket=self.bucket,
                    provider="local",
                    size=prefix_path.stat().st_size,
                )
            )

        return results

    async def delete(self, key: str) -> bool:
        """Delete the object at the given key"""
        path = self._get_full_path(key)
        if path.exists():
            path.unlink()
            # Also delete metadata file if exists
            meta_path = Path(str(path) + ".meta")
            if meta_path.exists():
                meta_path.unlink()
            return True
        return False

    async def presign_get(self, key: str, expires_sec: int = 3600) -> str:
        """Generate a file:// URL for local files"""
        path = self._get_full_path(key)
        return f"file://{quote(str(path.absolute()))}"

    async def presign_put(
        self, key: str, content_type: str | None = None, expires_sec: int = 3600
    ) -> str:
        """Generate a file:// URL for local files"""
        path = self._get_full_path(key)
        return f"file://{quote(str(path.absolute()))}"
