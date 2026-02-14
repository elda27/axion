from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from axion_server.apps.api.routers.batches import (
    create_batch,
    get_batch,
    list_batches,
)
from axion_server.shared.domain import BatchCreate


def _project(*, project_id: str = "proj-1"):
    return SimpleNamespace(project_id=project_id)


def _batch(
    *, batch_id: str = "batch-1", project_id: str = "proj-1", name: str = "Batch A"
):
    return SimpleNamespace(
        batch_id=batch_id,
        project_id=project_id,
        name=name,
        created_at=datetime(2026, 2, 12, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_create_batch_returns_response() -> None:
    project = _project()
    repo = Mock()
    batch = _batch()
    repo.create = AsyncMock(return_value=batch)

    data = BatchCreate(name="Batch A")
    response = await create_batch(data=data, project=project, repo=repo)

    repo.create.assert_awaited_once_with("proj-1", data)
    assert response.batch_id == "batch-1"
    assert response.project_id == "proj-1"
    assert response.name == "Batch A"


@pytest.mark.asyncio
async def test_list_batches_returns_cursor_page() -> None:
    project = _project()
    repo = Mock()
    batches = [_batch(batch_id="batch-1"), _batch(batch_id="batch-2")]
    repo.list_by_project = AsyncMock(return_value=(batches, "next-cursor"))

    page = await list_batches(project=project, repo=repo, limit=2, cursor="cur-1")

    repo.list_by_project.assert_awaited_once_with("proj-1", limit=2, cursor="cur-1")
    assert page.has_more is True
    assert page.next_cursor == "next-cursor"
    assert [item.batch_id for item in page.items] == ["batch-1", "batch-2"]


@pytest.mark.asyncio
async def test_list_batches_has_more_false_without_cursor() -> None:
    project = _project()
    repo = Mock()
    repo.list_by_project = AsyncMock(return_value=([_batch()], None))

    page = await list_batches(project=project, repo=repo)

    assert page.has_more is False
    assert page.next_cursor is None
    assert len(page.items) == 1


@pytest.mark.asyncio
async def test_get_batch_returns_validated_response() -> None:
    batch = _batch(batch_id="batch-99", name="Test Batch")

    response = await get_batch(batch=batch)

    assert response.batch_id == "batch-99"
    assert response.name == "Test Batch"
