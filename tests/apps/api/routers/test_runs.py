from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from axion_server.apps.api.routers.runs import (
    create_run,
    get_run,
    get_runs_summary,
    list_runs,
    update_run,
)
from axion_server.shared.domain import RunCreate, RunStatus, RunUpdate


def _batch(*, batch_id: str = "batch-1"):
    return SimpleNamespace(batch_id=batch_id)


def _run(
    *,
    run_id: str = "run-1",
    batch_id: str = "batch-1",
    name: str = "Run A",
    status: RunStatus = RunStatus.ACTIVE,
    tags: str = "[]",
    note: str | None = None,
):
    return SimpleNamespace(
        run_id=run_id,
        batch_id=batch_id,
        name=name,
        status=status,
        tags=tags,
        note=note,
        created_at=datetime(2026, 2, 12, tzinfo=UTC),
        updated_at=datetime(2026, 2, 12, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_create_run_returns_response() -> None:
    batch = _batch()
    repo = Mock()
    run = _run()
    repo.create = AsyncMock(return_value=run)

    data = RunCreate(name="Run A")
    response = await create_run(data=data, batch=batch, repo=repo)

    repo.create.assert_awaited_once_with("batch-1", data)
    assert response.run_id == "run-1"
    assert response.batch_id == "batch-1"
    assert response.name == "Run A"


@pytest.mark.asyncio
async def test_list_runs_returns_cursor_page() -> None:
    batch = _batch()
    repo = Mock()
    runs = [_run(run_id="run-1"), _run(run_id="run-2")]
    repo.list_by_batch = AsyncMock(return_value=(runs, "next-cursor"))

    page = await list_runs(batch=batch, repo=repo, limit=2, cursor="cur-1")

    repo.list_by_batch.assert_awaited_once_with(
        "batch-1",
        status=None,
        include_garbage=False,
        tag=None,
        q=None,
        limit=2,
        cursor="cur-1",
    )
    assert page.has_more is True
    assert page.next_cursor == "next-cursor"
    assert [item.run_id for item in page.items] == ["run-1", "run-2"]


@pytest.mark.asyncio
async def test_list_runs_with_filters() -> None:
    batch = _batch()
    repo = Mock()
    repo.list_by_batch = AsyncMock(return_value=([_run()], None))

    page = await list_runs(
        batch=batch,
        repo=repo,
        status=RunStatus.ACTIVE,
        include_garbage=True,
        tag="v1",
        q="search",
    )

    repo.list_by_batch.assert_awaited_once_with(
        "batch-1",
        status=RunStatus.ACTIVE,
        include_garbage=True,
        tag="v1",
        q="search",
        limit=20,
        cursor=None,
    )
    assert page.has_more is False


@pytest.mark.asyncio
async def test_get_runs_summary_full() -> None:
    batch = _batch()
    repo = Mock()

    champion = _run(run_id="champ-1", name="Champion")
    user_selected = [_run(run_id="us-1", name="UserSel")]
    recent = [_run(run_id="rec-1", name="Recent"), _run(run_id="rec-2", name="Recent2")]
    others_list = [
        _run(run_id="oth-1", name="Other"),
        _run(run_id="champ-1", name="Champion"),  # Should be filtered out
    ]

    repo.get_champion = AsyncMock(return_value=champion)
    repo.get_user_selected = AsyncMock(return_value=user_selected)
    repo.get_recent = AsyncMock(return_value=recent)
    repo.list_by_batch = AsyncMock(return_value=(others_list, "next-cur"))

    summary = await get_runs_summary(batch=batch, repo=repo)

    assert summary.champion is not None
    assert summary.champion.run_id == "champ-1"
    assert len(summary.user_selected) == 1
    assert summary.user_selected[0].run_id == "us-1"
    assert len(summary.recent_collapsed.runs) == 2
    assert summary.recent_collapsed.default_open is False
    # "champ-1" is in exclude_ids, so others should filter it out
    assert all(r.run_id != "champ-1" for r in summary.others.runs)
    assert summary.others.cursor == "next-cur"


@pytest.mark.asyncio
async def test_get_runs_summary_no_champion() -> None:
    batch = _batch()
    repo = Mock()

    repo.get_champion = AsyncMock(return_value=None)
    repo.get_user_selected = AsyncMock(return_value=[])
    repo.get_recent = AsyncMock(return_value=[])
    repo.list_by_batch = AsyncMock(return_value=([], None))

    summary = await get_runs_summary(batch=batch, repo=repo)

    assert summary.champion is None
    assert summary.user_selected == []
    assert summary.recent_collapsed.runs == []
    assert summary.others.runs == []
    assert summary.others.cursor is None


@pytest.mark.asyncio
async def test_get_run_returns_validated_response() -> None:
    run = _run(run_id="run-99", name="Test Run")

    response = await get_run(run=run)

    assert response.run_id == "run-99"
    assert response.name == "Test Run"


@pytest.mark.asyncio
async def test_update_run_returns_updated() -> None:
    run = _run(run_id="run-1")
    updated_run = _run(run_id="run-1", name="Updated Name")
    repo = Mock()
    repo.update = AsyncMock(return_value=updated_run)

    data = RunUpdate(name="Updated Name")
    response = await update_run(data=data, run=run, repo=repo)

    repo.update.assert_awaited_once_with("run-1", data)
    assert response.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_run_raises_on_unexpected_failure() -> None:
    run = _run(run_id="run-1")
    repo = Mock()
    repo.update = AsyncMock(return_value=None)

    data = RunUpdate(name="New Name")

    with pytest.raises(RuntimeError, match="Run update failed unexpectedly"):
        await update_run(data=data, run=run, repo=repo)
