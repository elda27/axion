import pytest

from axion_lab_server.gateways.storage.local import LocalObjectStore


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

    @pytest.mark.asyncio
    async def test_put_bytes_empty_data(self, store) -> None:
        ref = await store.put_bytes("empty.bin", b"")

        assert ref.size == 0
        data = await store.get_bytes("empty.bin")
        assert data == b""

    @pytest.mark.asyncio
    async def test_put_bytes_overwrites_existing(self, store) -> None:
        await store.put_bytes("overwrite.txt", b"old")
        ref = await store.put_bytes("overwrite.txt", b"new-data")

        assert ref.size == 8
        data = await store.get_bytes("overwrite.txt")
        assert data == b"new-data"

    @pytest.mark.asyncio
    async def test_put_bytes_with_only_content_type(self, store) -> None:
        ref = await store.put_bytes("typed.bin", b"data", content_type="text/plain")

        assert ref.content_type == "text/plain"
        assert ref.metadata is None

    @pytest.mark.asyncio
    async def test_put_bytes_with_only_metadata(self, store) -> None:
        ref = await store.put_bytes("meta.bin", b"data", metadata={"k": "v"})

        assert ref.content_type is None
        assert ref.metadata == {"k": "v"}

    @pytest.mark.asyncio
    async def test_put_bytes_deeply_nested_key(self, store) -> None:
        ref = await store.put_bytes("a/b/c/d/e/f.bin", b"deep")

        assert ref.key == "a/b/c/d/e/f.bin"
        data = await store.get_bytes("a/b/c/d/e/f.bin")
        assert data == b"deep"

    @pytest.mark.asyncio
    async def test_put_bytes_large_data(self, store) -> None:
        large = b"x" * 1_000_000
        ref = await store.put_bytes("large.bin", large)

        assert ref.size == 1_000_000
        data = await store.get_bytes("large.bin")
        assert data == large

    @pytest.mark.asyncio
    async def test_put_bytes_binary_content(self, store) -> None:
        binary = bytes(range(256))
        ref = await store.put_bytes("binary.bin", binary)

        assert ref.size == 256
        data = await store.get_bytes("binary.bin")
        assert data == binary


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

    @pytest.mark.asyncio
    async def test_put_and_get_json_list(self, store) -> None:
        data = [1, 2, 3, "four"]
        await store.put_json("list.json", data)

        result = await store.get_json("list.json")
        assert result == data

    @pytest.mark.asyncio
    async def test_put_and_get_json_nested(self, store) -> None:
        data = {"a": {"b": {"c": [1, 2, {"d": True}]}}}
        await store.put_json("nested.json", data)

        result = await store.get_json("nested.json")
        assert result == data

    @pytest.mark.asyncio
    async def test_put_json_unicode(self, store) -> None:
        data = {"emoji": "🚀", "chinese": "你好"}
        await store.put_json("unicode.json", data)

        result = await store.get_json("unicode.json")
        assert result == data

    @pytest.mark.asyncio
    async def test_get_json_raises_on_missing(self, store) -> None:
        with pytest.raises(FileNotFoundError, match="Object not found"):
            await store.get_json("missing.json")

    @pytest.mark.asyncio
    async def test_put_json_null_value(self, store) -> None:
        data = {"key": None}
        await store.put_json("null.json", data)

        result = await store.get_json("null.json")
        assert result == data

    @pytest.mark.asyncio
    async def test_put_json_empty_object(self, store) -> None:
        await store.put_json("empty.json", {})

        result = await store.get_json("empty.json")
        assert result == {}


class TestExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, store) -> None:
        await store.put_bytes("exists.txt", b"data")

        assert await store.exists("exists.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, store) -> None:
        assert await store.exists("nope.txt") is False

    @pytest.mark.asyncio
    async def test_exists_after_delete(self, store) -> None:
        await store.put_bytes("temp.txt", b"data")
        await store.delete("temp.txt")

        assert await store.exists("temp.txt") is False

    @pytest.mark.asyncio
    async def test_exists_nested_key(self, store) -> None:
        await store.put_bytes("a/b/c.txt", b"data")

        assert await store.exists("a/b/c.txt") is True
        assert await store.exists("a/b/d.txt") is False


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

    @pytest.mark.asyncio
    async def test_list_keys_excludes_meta_files(self, store) -> None:
        await store.put_bytes("dir/file.txt", b"data", metadata={"key": "val"})

        refs = await store.list_keys("dir")

        keys = [r.key for r in refs]
        assert len(keys) == 1
        assert not any(k.endswith(".meta") for k in keys)

    @pytest.mark.asyncio
    async def test_list_keys_nested_directory(self, store) -> None:
        await store.put_bytes("root/sub1/a.txt", b"a")
        await store.put_bytes("root/sub2/b.txt", b"b")

        refs = await store.list_keys("root")

        keys = sorted([r.key for r in refs])
        assert len(keys) == 2

    @pytest.mark.asyncio
    async def test_list_keys_returns_correct_size(self, store) -> None:
        await store.put_bytes("sized/file.txt", b"12345")

        refs = await store.list_keys("sized")

        assert len(refs) == 1
        assert refs[0].size == 5

    @pytest.mark.asyncio
    async def test_list_keys_returns_correct_bucket_and_provider(self, store) -> None:
        await store.put_bytes("meta-check/f.txt", b"x")

        refs = await store.list_keys("meta-check")

        assert refs[0].bucket == "test-bucket"
        assert refs[0].provider == "local"


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

    @pytest.mark.asyncio
    async def test_delete_idempotent(self, store) -> None:
        await store.put_bytes("once.txt", b"data")

        assert await store.delete("once.txt") is True
        assert await store.delete("once.txt") is False

    @pytest.mark.asyncio
    async def test_delete_does_not_affect_other_files(self, store) -> None:
        await store.put_bytes("keep.txt", b"keep")
        await store.put_bytes("remove.txt", b"remove")

        await store.delete("remove.txt")

        assert await store.exists("keep.txt") is True
        data = await store.get_bytes("keep.txt")
        assert data == b"keep"

    @pytest.mark.asyncio
    async def test_delete_nested_file(self, store) -> None:
        await store.put_bytes("dir/nested.txt", b"data")

        result = await store.delete("dir/nested.txt")

        assert result is True
        assert await store.exists("dir/nested.txt") is False


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

    @pytest.mark.asyncio
    async def test_presign_get_nonexistent_key(self, store) -> None:
        url = await store.presign_get("does-not-exist.txt")

        assert url.startswith("file://")
        assert "does-not-exist.txt" in url

    @pytest.mark.asyncio
    async def test_presign_put_with_content_type(self, store) -> None:
        url = await store.presign_put("upload.pdf", content_type="application/pdf")

        assert url.startswith("file://")
        assert "upload.pdf" in url

    @pytest.mark.asyncio
    async def test_presign_get_nested_key(self, store) -> None:
        await store.put_bytes("a/b/c.txt", b"data")

        url = await store.presign_get("a/b/c.txt")

        assert url.startswith("file://")
        assert "c.txt" in url


class TestConstructor:
    def test_creates_base_directory(self, tmp_path) -> None:
        new_path = tmp_path / "new" / "dir"
        LocalObjectStore(base_path=str(new_path), bucket="b")

        assert new_path.exists()

    def test_default_bucket(self, tmp_path) -> None:
        store = LocalObjectStore(base_path=str(tmp_path))

        assert store.bucket == "local"

    def test_custom_bucket(self, tmp_path) -> None:
        store = LocalObjectStore(base_path=str(tmp_path), bucket="my-bucket")

        assert store.bucket == "my-bucket"


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, store) -> None:
        # Create
        ref = await store.put_bytes("lifecycle.txt", b"v1", metadata={"v": "1"})
        assert ref.size == 2

        # Read
        data = await store.get_bytes("lifecycle.txt")
        assert data == b"v1"

        # Update
        ref2 = await store.put_bytes("lifecycle.txt", b"v2-longer", metadata={"v": "2"})
        assert ref2.size == 9

        data2 = await store.get_bytes("lifecycle.txt")
        assert data2 == b"v2-longer"

        # List
        assert await store.exists("lifecycle.txt") is True

        # Delete
        assert await store.delete("lifecycle.txt") is True
        assert await store.exists("lifecycle.txt") is False

    @pytest.mark.asyncio
    async def test_multiple_files_in_same_directory(self, store) -> None:
        for i in range(5):
            await store.put_bytes(f"batch/file_{i}.txt", f"content_{i}".encode())

        refs = await store.list_keys("batch")
        assert len(refs) == 5

        for i in range(5):
            data = await store.get_bytes(f"batch/file_{i}.txt")
            assert data == f"content_{i}".encode()
