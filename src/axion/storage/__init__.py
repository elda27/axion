"""Object Storage Adapter package"""

from axion.storage.base import ObjectRef, ObjectStore
from axion.storage.factory import get_object_store

__all__ = [
    "ObjectStore",
    "ObjectRef",
    "get_object_store",
]
