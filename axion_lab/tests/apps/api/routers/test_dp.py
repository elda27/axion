from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from axion_lab_server.apps.api.routers.dp import (
    _build_dp_job_response,
    create_dp_job,
    get_dp_job,
)
from axion_lab_server.shared.domain import DPJobCreate, DPJobMode, DPJobStatus


def _batch(*, batch_id: str = "batch-1"):
    return SimpleNamespace(batch_id=batch_id)


def _job(
    *,
    job_id: str = "job-1",
    batch_id: str = "batch-1",
    mode: str = "active_only",
    recompute: int = 0,
    status: str = "queued",
):
    return SimpleNamespace(
        job_id=job_id,
        batch_id=batch_id,
        mode=mode,
        recompute=recompute,
        status=status,
        requested_by=None,
        created_at=datetime(2026, 2, 12, tzinfo=UTC),
        started_at=None,
        finished_at=None,
        error_text=None,
    )


def test_build_dp_job_response() -> None:
    job = _job()

    response = _build_dp_job_response(job)

    assert response.job_id == "job-1"
    assert response.batch_id == "batch-1"
    assert response.recompute is False
    assert response.status == DPJobStatus.QUEUED


def test_build_dp_job_response_with_recompute() -> None:
    job = _job(recompute=1)

    response = _build_dp_job_response(job)

    assert response.recompute is True


@pytest.mark.asyncio
async def test_create_dp_job_success() -> None:
    batch = _batch()
    repo = Mock()
    repo.has_running_job = AsyncMock(return_value=False)
    repo.create = AsyncMock(return_value=_job())
    background_tasks = Mock()

    data = DPJobCreate(mode=DPJobMode.ACTIVE_ONLY, recompute=False)
    response = await create_dp_job(
        data=data, batch=batch, repo=repo, background_tasks=background_tasks
    )

    repo.has_running_job.assert_awaited_once_with("batch-1")
    repo.create.assert_awaited_once_with("batch-1", data)
    background_tasks.add_task.assert_called_once()
    assert response.job_id == "job-1"


@pytest.mark.asyncio
async def test_create_dp_job_raises_409_when_running_job_exists() -> None:
    batch = _batch()
    repo = Mock()
    repo.has_running_job = AsyncMock(return_value=True)
    background_tasks = Mock()

    data = DPJobCreate(mode=DPJobMode.ACTIVE_ONLY, recompute=False)

    with pytest.raises(HTTPException) as exc_info:
        await create_dp_job(
            data=data, batch=batch, repo=repo, background_tasks=background_tasks
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "A DP job is already running for this batch"


@pytest.mark.asyncio
async def test_get_dp_job_success() -> None:
    repo = Mock()
    repo.get_by_id = AsyncMock(return_value=_job(job_id="job-99"))

    response = await get_dp_job(job_id="job-99", repo=repo)

    repo.get_by_id.assert_awaited_once_with("job-99")
    assert response.job_id == "job-99"


@pytest.mark.asyncio
async def test_get_dp_job_raises_404_when_missing() -> None:
    repo = Mock()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_dp_job(job_id="missing", repo=repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "DP Job not found: missing"
