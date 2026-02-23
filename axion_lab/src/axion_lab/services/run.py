"""Run service."""

from __future__ import annotations

from axion_lab.schemas import (
    CursorPaginatedResponse,
    RunCreate,
    RunResponse,
    RunStatus,
    RunSummaryResponse,
    RunUpdate,
)
from axion_lab.services._http import HttpTransport


class RunService:
    """CRUD operations for runs."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def create(
        self,
        batch_id: str,
        name: str,
        *,
        status: RunStatus = RunStatus.ACTIVE,
        tags: list[str] | None = None,
        note: str | None = None,
    ) -> RunResponse:
        """Create a new run in a batch."""
        body = RunCreate(
            name=name,
            status=status,
            tags=tags or [],
            note=note,
        )
        data = self._http.post(
            f"/batches/{batch_id}/runs",
            json=body.model_dump(),
        )
        return RunResponse.model_validate(data)

    def list(
        self,
        batch_id: str,
        *,
        status: RunStatus | None = None,
        include_garbage: bool = False,
        tag: str | None = None,
        q: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[RunResponse]:
        """List runs in a batch with optional filtering."""
        params: dict[str, object] = {
            "limit": limit,
            "include_garbage": include_garbage,
        }
        if status:
            params["status"] = status.value
        if tag:
            params["tag"] = tag
        if q:
            params["q"] = q
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/batches/{batch_id}/runs", params=params)
        return CursorPaginatedResponse[RunResponse].model_validate(data)

    def get(self, run_id: str) -> RunResponse:
        """Get a run by ID."""
        data = self._http.get(f"/runs/{run_id}")
        return RunResponse.model_validate(data)

    def update(
        self,
        run_id: str,
        *,
        name: str | None = None,
        status: RunStatus | str | None = None,
        tags: list[str] | None = None,
        note: str | None = None,
    ) -> RunResponse:
        """Update a run (partial update)."""
        resolved_status = RunStatus(status) if status is not None else None
        body = RunUpdate(name=name, status=resolved_status, tags=tags, note=note)
        # Only send non-None fields
        data = self._http.patch(
            f"/runs/{run_id}",
            json=body.model_dump(exclude_none=True),
        )
        return RunResponse.model_validate(data)

    def summary(
        self,
        batch_id: str,
        *,
        include_garbage: bool = False,
    ) -> RunSummaryResponse:
        """Get run summary (champion, recent, user_selected, others)."""
        params: dict[str, object] = {"include_garbage": include_garbage}
        data = self._http.get(f"/batches/{batch_id}/runs/summary", params=params)
        return RunSummaryResponse.model_validate(data)
