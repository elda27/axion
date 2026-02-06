"""Object Storage Adapter package"""

from axion_server.storage.base import ObjectRef, ObjectStore
from axion_server.storage.factory import get_object_store

__all__ = [
    "ObjectStore",
    "ObjectRef",
    "get_object_store",
]
