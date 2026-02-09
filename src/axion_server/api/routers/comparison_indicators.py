"""Comparison Indicators API router"""

import json

from fastapi import APIRouter

from axion.schemas import ComparisonIndicatorResponse, CursorPaginatedResponse
from axion_server.api.deps import BatchPath, CIRepo, RunPath

router = APIRouter(tags=["Comparison Indicators"])


def _build_ci_response(ci) -> ComparisonIndicatorResponse:
    """Build comparison indicator response"""
    value = json.loads(ci.value_json) if ci.value_json else None
    return ComparisonIndicatorResponse(
        ci_id=ci.ci_id,
        run_id=ci.run_id,
        key=ci.key,
        value=value,
        baseline_ref=ci.baseline_ref,
        computed_at=ci.computed_at,
        version=ci.version,
    )


@router.get(
    "/runs/{run_id}/comparison-indicators",
    response_model=list[ComparisonIndicatorResponse],
)
async def list_comparison_indicators_by_run(
    run: RunPath,
    repo: CIRepo,
) -> list[ComparisonIndicatorResponse]:
    """List comparison indicators for a run"""
    indicators = await repo.list_by_run(run.run_id)
    return [_build_ci_response(i) for i in indicators]


@router.get(
    "/batches/{batch_id}/comparison-indicators",
    response_model=CursorPaginatedResponse[ComparisonIndicatorResponse],
)
async def list_comparison_indicators_by_batch(
    batch: BatchPath,
    repo: CIRepo,
    key: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[ComparisonIndicatorResponse]:
    """List comparison indicators for a batch"""
    indicators, next_cursor = await repo.list_by_batch(
        batch.batch_id, key=key, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[_build_ci_response(i) for i in indicators],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )
