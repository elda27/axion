"""Object Storage base interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ObjectRef:
    """Reference to an object in storage"""

    key: str
    bucket: str
    provider: str
    size: int | None = None
    content_type: str | None = None
    metadata: dict[str, str] | None = None


class ObjectStore(ABC):
    """Abstract base class for object storage implementations"""

    @abstractmethod
    async def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store bytes at the given key"""
        ...

    @abstractmethod
    async def put_json(
        self,
        key: str,
        data: Any,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store JSON data at the given key"""
        ...

    @abstractmethod
    async def get_bytes(self, key: str) -> bytes:
        """Retrieve bytes from the given key"""
        ...

    @abstractmethod
    async def get_json(self, key: str) -> Any:
        """Retrieve JSON data from the given key"""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if an object exists at the given key"""
        ...

    @abstractmethod
    async def list_keys(self, prefix: str) -> list[ObjectRef]:
        """List objects with the given prefix"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete the object at the given key"""
        ...

    @abstractmethod
    async def presign_get(self, key: str, expires_sec: int = 3600) -> str:
        """Generate a presigned URL for GET operations"""
        ...

    @abstractmethod
    async def presign_put(
        self, key: str, content_type: str | None = None, expires_sec: int = 3600
    ) -> str:
        """Generate a presigned URL for PUT operations"""
        ...
