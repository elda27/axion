"""Artifact service."""

from __future__ import annotations

from typing import Any

from axion_lab.schemas import (
    ArtifactCreate,
    ArtifactKind,
    ArtifactResponse,
    CursorPaginatedResponse,
)
from axion_lab.services._http import HttpTransport


class ArtifactService:
    """CRUD operations for artifacts."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def create(
        self,
        run_id: str,
        *,
        kind: ArtifactKind | str,
        type: str,
        label: str,
        payload: Any,
        meta: dict[str, Any] | None = None,
    ) -> ArtifactResponse:
        """Create a new artifact for a run."""
        body = ArtifactCreate(
            kind=ArtifactKind(kind),
            type=type,
            label=label,
            payload=payload,
            meta=meta or {},
        )
        data = self._http.post(
            f"/runs/{run_id}/artifacts",
            json=body.model_dump(),
        )
        return ArtifactResponse.model_validate(data)

    def list(
        self,
        run_id: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[ArtifactResponse]:
        """List artifacts for a run."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/runs/{run_id}/artifacts", params=params)
        return CursorPaginatedResponse[ArtifactResponse].model_validate(data)

    def delete(self, artifact_id: str) -> None:
        """Delete an artifact by ID."""
        self._http.delete(f"/artifacts/{artifact_id}")
