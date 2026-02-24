"""Run Metric service."""

from __future__ import annotations

from axion_lab.schemas import CursorPaginatedResponse, RunMetricResponse
from axion_lab.services._http import HttpTransport


class RunMetricService:
    """Read-only access to run metrics (computed via DP)."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def list_by_run(
        self,
        run_id: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[RunMetricResponse]:
        """List run metrics for a run."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/runs/{run_id}/run-metrics", params=params)
        return CursorPaginatedResponse[RunMetricResponse].model_validate(data)

    def list_by_batch(
        self,
        batch_id: str,
        *,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[RunMetricResponse]:
        """List run metrics for all runs in a batch."""
        params: dict[str, object] = {"limit": limit}
        if key:
            params["key"] = key
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/batches/{batch_id}/run-metrics", params=params)
        return CursorPaginatedResponse[RunMetricResponse].model_validate(data)
