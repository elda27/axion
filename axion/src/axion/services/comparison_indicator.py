"""Comparison Indicator service."""

from __future__ import annotations

from axion.schemas import ComparisonIndicatorResponse, CursorPaginatedResponse
from axion.services._http import HttpTransport


class ComparisonIndicatorService:
    """Read-only access to comparison indicators (computed via DP)."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def list_by_run(
        self,
        run_id: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[ComparisonIndicatorResponse]:
        """List comparison indicators for a run."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/runs/{run_id}/comparison-indicators", params=params)
        return CursorPaginatedResponse[ComparisonIndicatorResponse].model_validate(data)

    def list_by_batch(
        self,
        batch_id: str,
        *,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[ComparisonIndicatorResponse]:
        """List comparison indicators for all runs in a batch."""
        params: dict[str, object] = {"limit": limit}
        if key:
            params["key"] = key
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(
            f"/batches/{batch_id}/comparison-indicators", params=params
        )
        return CursorPaginatedResponse[ComparisonIndicatorResponse].model_validate(data)
