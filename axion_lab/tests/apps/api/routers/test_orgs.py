from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from axion_lab_server.apps.api.routers.orgs import create_org, get_org, list_orgs
from axion_lab_server.shared.domain import OrgCreate


def _org(*, org_id: str = "org-1", name: str = "Acme Corp"):
    return SimpleNamespace(
        org_id=org_id,
        name=name,
        created_at=datetime(2026, 2, 12, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_create_org_returns_response() -> None:
    repo = Mock()
    org = _org()
    repo.create = AsyncMock(return_value=org)

    data = OrgCreate(name="Acme Corp")
    response = await create_org(data=data, repo=repo)

    repo.create.assert_awaited_once_with(data)
    assert response.org_id == "org-1"
    assert response.name == "Acme Corp"


@pytest.mark.asyncio
async def test_list_orgs_returns_cursor_page() -> None:
    repo = Mock()
    orgs = [_org(org_id="org-1"), _org(org_id="org-2")]
    repo.list_all = AsyncMock(return_value=(orgs, "next-cursor"))

    page = await list_orgs(repo=repo, limit=2, cursor="cur-1")

    repo.list_all.assert_awaited_once_with(limit=2, cursor="cur-1")
    assert page.has_more is True
    assert page.next_cursor == "next-cursor"
    assert [item.org_id for item in page.items] == ["org-1", "org-2"]


@pytest.mark.asyncio
async def test_list_orgs_has_more_false_without_cursor() -> None:
    repo = Mock()
    repo.list_all = AsyncMock(return_value=([_org()], None))

    page = await list_orgs(repo=repo)

    assert page.has_more is False
    assert page.next_cursor is None
    assert len(page.items) == 1


@pytest.mark.asyncio
async def test_get_org_returns_validated_response() -> None:
    org = _org(org_id="org-99", name="Test Org")

    response = await get_org(org=org)

    assert response.org_id == "org-99"
    assert response.name == "Test Org"
