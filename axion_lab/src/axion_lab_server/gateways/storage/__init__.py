"""Object Storage Adapter package"""

from axion_lab_server.gateways.storage.base import ObjectRef, ObjectStore
from axion_lab_server.gateways.storage.factory import get_object_store

__all__ = [
    "ObjectStore",
    "ObjectRef",
    "get_object_store",
]
