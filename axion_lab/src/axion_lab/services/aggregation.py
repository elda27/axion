"""Aggregation service."""

from __future__ import annotations

from typing import Any

from axion_lab.schemas import (
    AggregationMemberResponse,
    AggregationResponse,
    CursorPaginatedResponse,
)
from axion_lab.services._http import HttpTransport

_List = list  # alias to avoid shadowing by the `list` method


class AggregationService:
    """CRUD operations for aggregations and their members."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    # ── Aggregation CRUD ──────────────────────────────────────

    def create(
        self,
        project_id: str,
        name: str,
        *,
        description: str | None = None,
        group_by_keys: _List[str] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Create a new aggregation under a project."""
        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        if group_by_keys:
            payload["groupByKeys"] = group_by_keys
        if filter:
            payload["filter"] = filter
        data = self._http.post(
            f"/projects/{project_id}/aggregations",
            json=payload,
        )
        return AggregationResponse.model_validate(data)

    def list(
        self,
        project_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[AggregationResponse]:
        """List aggregations in a project."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/projects/{project_id}/aggregations", params=params)
        return CursorPaginatedResponse[AggregationResponse].model_validate(data)

    def get(self, aggregation_id: str) -> AggregationResponse:
        """Get an aggregation by ID."""
        data = self._http.get(f"/aggregations/{aggregation_id}")
        return AggregationResponse.model_validate(data)

    def delete(self, aggregation_id: str) -> None:
        """Delete an aggregation."""
        self._http.delete(f"/aggregations/{aggregation_id}")

    # ── Member management ─────────────────────────────────────

    def add_member(
        self,
        aggregation_id: str,
        run_id: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AggregationMemberResponse:
        """Add a run to an aggregation."""
        payload: dict[str, Any] = {"runId": run_id}
        if metadata:
            payload["metadata"] = metadata
        data = self._http.post(
            f"/aggregations/{aggregation_id}/members",
            json=payload,
        )
        return AggregationMemberResponse.model_validate(data)

    def list_members(
        self,
        aggregation_id: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[AggregationMemberResponse]:
        """List members of an aggregation."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/aggregations/{aggregation_id}/members", params=params)
        return CursorPaginatedResponse[AggregationMemberResponse].model_validate(data)

    def remove_member(self, aggregation_id: str, run_id: str) -> None:
        """Remove a run from an aggregation."""
        self._http.delete(f"/aggregations/{aggregation_id}/members/{run_id}")
