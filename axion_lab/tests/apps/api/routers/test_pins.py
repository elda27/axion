from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from axion_lab_server.apps.api.routers.pins import create_pin, delete_pin
from axion_lab_server.shared.domain import PinCreate, PinType


def _run(*, run_id: str = "run-1", batch_id: str = "batch-1"):
    return SimpleNamespace(run_id=run_id, batch_id=batch_id)


def _pin(*, run_id: str = "run-1", batch_id: str = "batch-1"):
    return SimpleNamespace(
        pin_id="pin-1",
        run_id=run_id,
        batch_id=batch_id,
        pin_type=PinType.CHAMPION,
        pinned_by=None,
        pinned_at=datetime(2026, 2, 12, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_create_pin_success() -> None:
    run = _run()
    repo = Mock()
    batch_repo = Mock()

    batch_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(batch_id="batch-1"))
    repo.get_by_run_and_type = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=_pin())

    data = PinCreate(pinType=PinType.CHAMPION)

    response = await create_pin(data=data, run=run, repo=repo, batch_repo=batch_repo)

    batch_repo.get_by_id.assert_awaited_once_with("batch-1")
    repo.get_by_run_and_type.assert_awaited_once_with("run-1", PinType.CHAMPION)
    repo.create.assert_awaited_once_with(
        run_id="run-1",
        batch_id="batch-1",
        pin_type=PinType.CHAMPION,
    )
    assert response.pin_id == "pin-1"
    assert response.run_id == "run-1"


@pytest.mark.asyncio
async def test_create_pin_raises_404_when_batch_missing() -> None:
    run = _run(batch_id="missing-batch")
    repo = Mock()
    batch_repo = Mock()

    batch_repo.get_by_id = AsyncMock(return_value=None)

    data = PinCreate(pinType=PinType.CHAMPION)

    with pytest.raises(HTTPException) as exc_info:
        await create_pin(data=data, run=run, repo=repo, batch_repo=batch_repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Batch not found: missing-batch"


@pytest.mark.asyncio
async def test_create_pin_raises_409_when_duplicate_exists() -> None:
    run = _run()
    repo = Mock()
    batch_repo = Mock()

    batch_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(batch_id="batch-1"))
    repo.get_by_run_and_type = AsyncMock(return_value=_pin())

    data = PinCreate(pinType=PinType.USER_SELECTED)

    with pytest.raises(HTTPException) as exc_info:
        await create_pin(data=data, run=run, repo=repo, batch_repo=batch_repo)

    assert exc_info.value.status_code == 409
    assert (
        exc_info.value.detail
        == "Pin already exists for run run-1 with type user_selected"
    )


@pytest.mark.asyncio
async def test_delete_pin_success() -> None:
    run = _run()
    repo = Mock()
    repo.delete_by_run_and_type = AsyncMock(return_value=True)

    result = await delete_pin(run=run, pin_type=PinType.CHAMPION, repo=repo)

    repo.delete_by_run_and_type.assert_awaited_once_with("run-1", PinType.CHAMPION)
    assert result is None


@pytest.mark.asyncio
async def test_delete_pin_raises_404_when_missing() -> None:
    run = _run(run_id="run-x")
    repo = Mock()
    repo.delete_by_run_and_type = AsyncMock(return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        await delete_pin(run=run, pin_type=PinType.USER_SELECTED, repo=repo)

    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail == "Pin not found for run run-x with type user_selected"
    )
