"""Batch service."""

from __future__ import annotations

from axion.schemas import BatchCreate, BatchResponse, CursorPaginatedResponse
from axion.services._http import HttpTransport


class BatchService:
    """CRUD operations for batches."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def create(self, project_id: str, name: str) -> BatchResponse:
        """Create a new batch under a project."""
        data = self._http.post(
            f"/projects/{project_id}/batches",
            json=BatchCreate(name=name).model_dump(),
        )
        return BatchResponse.model_validate(data)

    def list(
        self,
        project_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[BatchResponse]:
        """List batches in a project."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/projects/{project_id}/batches", params=params)
        return CursorPaginatedResponse[BatchResponse].model_validate(data)

    def get(self, batch_id: str) -> BatchResponse:
        """Get a batch by ID."""
        data = self._http.get(f"/batches/{batch_id}")
        return BatchResponse.model_validate(data)
