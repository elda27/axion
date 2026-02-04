"""Quality Metrics API router"""

import json

from fastapi import APIRouter

from axion.api.deps import BatchPath, QMRepo, RunPath
from axion.schemas import CursorPaginatedResponse, QualityMetricResponse

router = APIRouter(tags=["Quality Metrics"])


def _build_qm_response(qm) -> QualityMetricResponse:
    """Build quality metric response"""
    value = json.loads(qm.value_json) if qm.value_json else None
    return QualityMetricResponse(
        qm_id=qm.qm_id,
        run_id=qm.run_id,
        key=qm.key,
        value=value,
        source=qm.source,
        computed_at=qm.computed_at,
        version=qm.version,
    )


@router.get(
    "/runs/{run_id}/quality-metrics",
    response_model=list[QualityMetricResponse],
)
async def list_quality_metrics_by_run(
    run: RunPath,
    repo: QMRepo,
) -> list[QualityMetricResponse]:
    """List quality metrics for a run"""
    metrics = await repo.list_by_run(run.run_id)
    return [_build_qm_response(m) for m in metrics]


@router.get(
    "/batches/{batch_id}/quality-metrics",
    response_model=CursorPaginatedResponse[QualityMetricResponse],
)
async def list_quality_metrics_by_batch(
    batch: BatchPath,
    repo: QMRepo,
    key: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[QualityMetricResponse]:
    """List quality metrics for a batch"""
    metrics, next_cursor = await repo.list_by_batch(
        batch.batch_id, key=key, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[_build_qm_response(m) for m in metrics],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )
