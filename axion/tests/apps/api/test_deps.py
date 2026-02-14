from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from axion_server.apps.api.deps import (
    get_batch_or_404,
    get_org_or_404,
    get_project_or_404,
    get_run_or_404,
)


@pytest.mark.asyncio
async def test_get_org_or_404_returns_org() -> None:
    repo = Mock()
    org = Mock(org_id="org-1")
    repo.get_by_id = AsyncMock(return_value=org)

    result = await get_org_or_404(org_id="org-1", repo=repo)

    repo.get_by_id.assert_awaited_once_with("org-1")
    assert result.org_id == "org-1"


@pytest.mark.asyncio
async def test_get_org_or_404_raises_404() -> None:
    repo = Mock()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_org_or_404(org_id="missing", repo=repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Organization not found: missing"


@pytest.mark.asyncio
async def test_get_project_or_404_returns_project() -> None:
    repo = Mock()
    project = Mock(project_id="proj-1")
    repo.get_by_id = AsyncMock(return_value=project)

    result = await get_project_or_404(project_id="proj-1", repo=repo)

    repo.get_by_id.assert_awaited_once_with("proj-1")
    assert result.project_id == "proj-1"


@pytest.mark.asyncio
async def test_get_project_or_404_raises_404() -> None:
    repo = Mock()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_project_or_404(project_id="missing", repo=repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found: missing"


@pytest.mark.asyncio
async def test_get_batch_or_404_returns_batch() -> None:
    repo = Mock()
    batch = Mock(batch_id="batch-1")
    repo.get_by_id = AsyncMock(return_value=batch)

    result = await get_batch_or_404(batch_id="batch-1", repo=repo)

    repo.get_by_id.assert_awaited_once_with("batch-1")
    assert result.batch_id == "batch-1"


@pytest.mark.asyncio
async def test_get_batch_or_404_raises_404() -> None:
    repo = Mock()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_batch_or_404(batch_id="missing", repo=repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Batch not found: missing"


@pytest.mark.asyncio
async def test_get_run_or_404_returns_run() -> None:
    repo = Mock()
    run = Mock(run_id="run-1")
    repo.get_by_id = AsyncMock(return_value=run)

    result = await get_run_or_404(run_id="run-1", repo=repo)

    repo.get_by_id.assert_awaited_once_with("run-1")
    assert result.run_id == "run-1"


@pytest.mark.asyncio
async def test_get_run_or_404_raises_404() -> None:
    repo = Mock()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_run_or_404(run_id="missing", repo=repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Run not found: missing"
