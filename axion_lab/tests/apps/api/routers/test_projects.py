from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from axion_lab_server.apps.api.routers.projects import (
    create_project,
    get_project,
    list_projects,
)
from axion_lab_server.shared.domain import ProjectCreate


def _org(*, org_id: str = "org-1"):
    return SimpleNamespace(org_id=org_id)


def _project(
    *, project_id: str = "proj-1", org_id: str = "org-1", name: str = "My Project"
):
    return SimpleNamespace(
        project_id=project_id,
        org_id=org_id,
        name=name,
        created_at=datetime(2026, 2, 12, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_create_project_returns_response() -> None:
    org = _org()
    repo = Mock()
    project = _project()
    repo.get_by_name = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=project)

    data = ProjectCreate(name="My Project")
    response = await create_project(data=data, org=org, repo=repo)

    repo.get_by_name.assert_awaited_once_with("org-1", "My Project")
    repo.create.assert_awaited_once_with("org-1", data)
    assert response.project_id == "proj-1"
    assert response.org_id == "org-1"
    assert response.name == "My Project"


@pytest.mark.asyncio
async def test_create_project_raises_409_when_name_exists() -> None:
    org = _org()
    repo = Mock()
    repo.get_by_name = AsyncMock(return_value=_project())

    data = ProjectCreate(name="My Project")

    with pytest.raises(HTTPException) as exc_info:
        await create_project(data=data, org=org, repo=repo)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_projects_returns_cursor_page() -> None:
    org = _org()
    repo = Mock()
    projects = [_project(project_id="proj-1"), _project(project_id="proj-2")]
    repo.list_by_org = AsyncMock(return_value=(projects, "next-cursor"))

    page = await list_projects(org=org, repo=repo, limit=2, cursor="cur-1")

    repo.list_by_org.assert_awaited_once_with("org-1", limit=2, cursor="cur-1")
    assert page.has_more is True
    assert page.next_cursor == "next-cursor"
    assert [item.project_id for item in page.items] == ["proj-1", "proj-2"]


@pytest.mark.asyncio
async def test_list_projects_has_more_false_without_cursor() -> None:
    org = _org()
    repo = Mock()
    repo.list_by_org = AsyncMock(return_value=([_project()], None))

    page = await list_projects(org=org, repo=repo)

    assert page.has_more is False
    assert page.next_cursor is None
    assert len(page.items) == 1


@pytest.mark.asyncio
async def test_get_project_returns_validated_response() -> None:
    project = _project(project_id="proj-99", name="Test Project")

    response = await get_project(project=project)

    assert response.project_id == "proj-99"
    assert response.name == "Test Project"
