"""Artifact API router"""

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Path, status

from axion_server.apps.api.deps import ArtifactRepo, RunPath
from axion_server.shared.domain import (
    ArtifactCreate,
    ArtifactResponse,
    CursorPaginatedResponse,
)

router = APIRouter(tags=["Artifacts"])


def _build_artifact_response(artifact: Any, repo: ArtifactRepo) -> ArtifactResponse:
    """Build artifact response with proper payload"""
    payload = repo.get_payload(artifact)
    meta = json.loads(artifact.meta_json) if artifact.meta_json else {}

    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        run_id=artifact.run_id,
        kind=artifact.kind,
        type=artifact.type,
        label=artifact.label,
        payload=payload,
        meta=meta,
        created_at=artifact.created_at,
    )


@router.post(
    "/runs/{run_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact(
    data: ArtifactCreate,
    run: RunPath,
    repo: ArtifactRepo,
) -> ArtifactResponse:
    """Create a new artifact for a run"""
    artifact = await repo.create(run.run_id, data)
    return _build_artifact_response(artifact, repo)


@router.get(
    "/runs/{run_id}/artifacts",
    response_model=CursorPaginatedResponse[ArtifactResponse],
)
async def list_artifacts(
    run: RunPath,
    repo: ArtifactRepo,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[ArtifactResponse]:
    """List artifacts for a run"""
    artifacts, next_cursor = await repo.list_by_run(
        run.run_id, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[_build_artifact_response(a, repo) for a in artifacts],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.delete(
    "/artifacts/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_artifact(
    artifact_id: str = Path(),
    repo: ArtifactRepo = ...,
) -> None:
    """Delete an artifact"""
    deleted = await repo.delete(artifact_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}",
        )
