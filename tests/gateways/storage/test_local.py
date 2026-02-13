import pytest

from axion_server.gateways.storage.local import LocalObjectStore


@pytest.fixture
def store(tmp_path):
    return LocalObjectStore(base_path=str(tmp_path), bucket="test-bucket")


class TestPutAndGetBytes:
    @pytest.mark.asyncio
    async def test_put_and_get_bytes(self, store) -> None:
        ref = await store.put_bytes("test/file.bin", b"hello")

        assert ref.key == "test/file.bin"
        assert ref.bucket == "test-bucket"
        assert ref.provider == "local"
        assert ref.size == 5

        data = await store.get_bytes("test/file.bin")
        assert data == b"hello"

    @pytest.mark.asyncio
    async def test_put_bytes_with_content_type_and_metadata(self, store) -> None:
        ref = await store.put_bytes(
            "doc.pdf",
            b"pdf-data",
            content_type="application/pdf",
            metadata={"author": "test"},
        )

        assert ref.content_type == "application/pdf"
        assert ref.metadata == {"author": "test"}

    @pytest.mark.asyncio
    async def test_get_bytes_raises_on_missing(self, store) -> None:
        with pytest.raises(FileNotFoundError, match="Object not found"):
            await store.get_bytes("nonexistent")


class TestPutAndGetJson:
    @pytest.mark.asyncio
    async def test_put_and_get_json(self, store) -> None:
        data = {"key": "value", "number": 42}
        ref = await store.put_json("data.json", data)

        assert ref.content_type == "application/json"

        result = await store.get_json("data.json")
        assert result == data

    @pytest.mark.asyncio
    async def test_put_json_with_metadata(self, store) -> None:
        ref = await store.put_json("meta.json", {"a": 1}, metadata={"version": "1"})
        assert ref.metadata == {"version": "1"}


class TestExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, store) -> None:
        await store.put_bytes("exists.txt", b"data")

        assert await store.exists("exists.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, store) -> None:
        assert await store.exists("nope.txt") is False


class TestListKeys:
    @pytest.mark.asyncio
    async def test_list_keys_in_directory(self, store) -> None:
        await store.put_bytes("prefix/a.txt", b"a")
        await store.put_bytes("prefix/b.txt", b"b")
        await store.put_bytes("other/c.txt", b"c")

        refs = await store.list_keys("prefix")

        keys = sorted([r.key for r in refs])
        assert len(keys) == 2
        assert all("prefix" in k for k in keys)

    @pytest.mark.asyncio
    async def test_list_keys_single_file(self, store) -> None:
        await store.put_bytes("single.txt", b"data")

        refs = await store.list_keys("single.txt")

        assert len(refs) == 1
        assert refs[0].key == "single.txt"

    @pytest.mark.asyncio
    async def test_list_keys_empty(self, store) -> None:
        refs = await store.list_keys("nonexistent")

        assert refs == []


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_existing(self, store) -> None:
        await store.put_bytes("to-delete.txt", b"data")

        result = await store.delete("to-delete.txt")

        assert result is True
        assert await store.exists("to-delete.txt") is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store) -> None:
        result = await store.delete("nope.txt")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_metadata_sidecar(self, store) -> None:
        await store.put_bytes("with-meta.txt", b"data", metadata={"key": "val"})

        assert await store.delete("with-meta.txt") is True
        assert await store.exists("with-meta.txt") is False


class TestPresign:
    @pytest.mark.asyncio
    async def test_presign_get_returns_file_url(self, store) -> None:
        await store.put_bytes("signed.txt", b"data")

        url = await store.presign_get("signed.txt")

        assert url.startswith("file://")
        assert "signed.txt" in url

    @pytest.mark.asyncio
    async def test_presign_put_returns_file_url(self, store) -> None:
        url = await store.presign_put("upload.txt")

        assert url.startswith("file://")
        assert "upload.txt" in url
