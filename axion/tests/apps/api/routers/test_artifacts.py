from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from axion_server.apps.api.routers.artifacts import (
    _build_artifact_response,
    create_artifact,
    delete_artifact,
    list_artifacts,
)
from axion_server.shared.domain import ArtifactCreate, ArtifactKind


def _artifact(*, artifact_id: str = "a1", run_id: str = "r1", meta_json: str = ""):
    return SimpleNamespace(
        artifact_id=artifact_id,
        run_id=run_id,
        kind=ArtifactKind.INLINE_JSON,
        type="evaluation",
        label="summary",
        meta_json=meta_json,
        created_at=datetime(2026, 2, 12, tzinfo=UTC),
    )


def test_build_artifact_response_parses_payload_and_meta() -> None:
    artifact = _artifact(meta_json='{"score": 0.91}')
    repo = Mock()
    repo.get_payload.return_value = {"result": "ok"}

    response = _build_artifact_response(artifact, repo)

    assert response.artifact_id == "a1"
    assert response.run_id == "r1"
    assert response.payload == {"result": "ok"}
    assert response.meta == {"score": 0.91}


@pytest.mark.asyncio
async def test_create_artifact_returns_built_response() -> None:
    run = SimpleNamespace(run_id="run-123")
    artifact = _artifact(artifact_id="art-1", run_id="run-123")
    repo = Mock()
    repo.create = AsyncMock(return_value=artifact)
    repo.get_payload.return_value = {"message": "created"}

    data = ArtifactCreate(
        kind=ArtifactKind.INLINE_JSON,
        type="evaluation",
        label="result",
        payload={"input": 1},
        meta={"source": "test"},
    )

    response = await create_artifact(data=data, run=run, repo=repo)

    repo.create.assert_awaited_once_with("run-123", data)
    assert response.artifact_id == "art-1"
    assert response.run_id == "run-123"
    assert response.payload == {"message": "created"}


@pytest.mark.asyncio
async def test_list_artifacts_returns_cursor_page() -> None:
    run = SimpleNamespace(run_id="run-321")
    artifacts = [
        _artifact(artifact_id="a1", run_id="run-321"),
        _artifact(artifact_id="a2", run_id="run-321"),
    ]

    repo = Mock()
    repo.list_by_run = AsyncMock(return_value=(artifacts, "next-cursor"))
    repo.get_payload.side_effect = [{"idx": 1}, {"idx": 2}]

    page = await list_artifacts(run=run, repo=repo, limit=2, cursor="cur-1")

    repo.list_by_run.assert_awaited_once_with("run-321", limit=2, cursor="cur-1")
    assert page.has_more is True
    assert page.next_cursor == "next-cursor"
    assert [item.artifact_id for item in page.items] == ["a1", "a2"]


@pytest.mark.asyncio
async def test_delete_artifact_returns_none_on_success() -> None:
    repo = Mock()
    repo.delete = AsyncMock(return_value=True)

    result = await delete_artifact(artifact_id="a1", repo=repo)

    repo.delete.assert_awaited_once_with("a1")
    assert result is None


@pytest.mark.asyncio
async def test_delete_artifact_raises_404_when_missing() -> None:
    repo = Mock()
    repo.delete = AsyncMock(return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        await delete_artifact(artifact_id="missing", repo=repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Artifact not found: missing"
