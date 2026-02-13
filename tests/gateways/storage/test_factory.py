from unittest.mock import patch

import pytest

from axion_server.gateways.storage.factory import get_object_store
from axion_server.gateways.storage.gcs import GCSObjectStore
from axion_server.gateways.storage.local import LocalObjectStore
from axion_server.gateways.storage.s3 import S3ObjectStore


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear lru_cache before each test"""
    get_object_store.cache_clear()
    yield
    get_object_store.cache_clear()


def _mock_settings(**overrides):
    defaults = {
        "object_store_provider": "local",
        "object_store_local_path": "/tmp/test-store",
        "object_store_bucket": "test-bucket",
        "gcs_project_id": "test-project",
        "gcs_credentials_path": None,
        "object_store_endpoint": None,
        "object_store_access_key": None,
        "object_store_secret_key": None,
        "object_store_region": None,
    }
    defaults.update(overrides)

    class FakeSettings:
        pass

    s = FakeSettings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


@patch("axion_server.gateways.storage.factory.get_settings")
def test_factory_returns_local_store(mock_get_settings) -> None:
    mock_get_settings.return_value = _mock_settings(object_store_provider="local")

    store = get_object_store()

    assert isinstance(store, LocalObjectStore)


@patch("axion_server.gateways.storage.factory.get_settings")
def test_factory_returns_gcs_store(mock_get_settings) -> None:
    mock_get_settings.return_value = _mock_settings(object_store_provider="gcs")

    store = get_object_store()

    assert isinstance(store, GCSObjectStore)


@patch("axion_server.gateways.storage.factory.get_settings")
def test_factory_returns_s3_store(mock_get_settings) -> None:
    mock_get_settings.return_value = _mock_settings(object_store_provider="s3")

    store = get_object_store()

    assert isinstance(store, S3ObjectStore)


@patch("axion_server.gateways.storage.factory.get_settings")
def test_factory_returns_s3_for_minio(mock_get_settings) -> None:
    mock_get_settings.return_value = _mock_settings(
        object_store_provider="minio",
        object_store_endpoint="http://localhost:9000",
    )

    store = get_object_store()

    assert isinstance(store, S3ObjectStore)
