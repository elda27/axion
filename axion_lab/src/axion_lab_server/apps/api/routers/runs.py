"""Run API router"""

from fastapi import APIRouter, status

from axion_lab_server.apps.api.deps import BatchPath, RunPath, RunRepo
from axion_lab_server.shared.domain import (
    CursorPaginatedResponse,
    RunCreate,
    RunResponse,
    RunStatus,
    RunSummaryResponse,
    RunUpdate,
)
from axion_lab_server.shared.domain.run import (
    OthersSection,
    RecentCollapsed,
    RunBriefResponse,
)

router = APIRouter(tags=["Runs"])


@router.post(
    "/batches/{batch_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_run(
    data: RunCreate,
    batch: BatchPath,
    repo: RunRepo,
) -> RunResponse:
    """Create a new run in a batch"""
    run = await repo.create(batch.batch_id, data)
    return RunResponse.model_validate(run)


@router.get(
    "/batches/{batch_id}/runs",
    response_model=CursorPaginatedResponse[RunResponse],
)
async def list_runs(
    batch: BatchPath,
    repo: RunRepo,
    status: RunStatus | None = None,
    include_garbage: bool = False,
    tag: str | None = None,
    q: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> CursorPaginatedResponse[RunResponse]:
    """List runs in a batch with filtering"""
    runs, next_cursor = await repo.list_by_batch(
        batch.batch_id,
        status=status,
        include_garbage=include_garbage,
        tag=tag,
        q=q,
        limit=limit,
        cursor=cursor,
    )
    return CursorPaginatedResponse(
        items=[RunResponse.model_validate(r) for r in runs],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get(
    "/batches/{batch_id}/runs/summary",
    response_model=RunSummaryResponse,
)
async def get_runs_summary(
    batch: BatchPath,
    repo: RunRepo,
    include_garbage: bool = False,
) -> RunSummaryResponse:
    """Get run summary with champion, recent, user_selected, and others"""
    # Get champion
    champion = await repo.get_champion(batch.batch_id)

    # Get user selected
    user_selected = await repo.get_user_selected(batch.batch_id)

    # Collect IDs to exclude from recent and others
    exclude_ids: list[str] = []
    if champion:
        exclude_ids.append(champion.run_id)
    exclude_ids.extend([r.run_id for r in user_selected])

    # Get recent 3
    recent = await repo.get_recent(batch.batch_id, limit=3, exclude_ids=exclude_ids)
    exclude_ids.extend([r.run_id for r in recent])

    # Get others
    others, next_cursor = await repo.list_by_batch(
        batch.batch_id,
        include_garbage=include_garbage,
        limit=10,
    )
    # Filter out already included runs
    others = [r for r in others if r.run_id not in exclude_ids]

    return RunSummaryResponse(
        champion=RunBriefResponse.model_validate(champion) if champion else None,
        recentCollapsed=RecentCollapsed(
            default_open=False,
            runs=[RunBriefResponse.model_validate(r) for r in recent],
        ),
        userSelected=[RunBriefResponse.model_validate(r) for r in user_selected],
        others=OthersSection(
            cursor=next_cursor,
            runs=[RunBriefResponse.model_validate(r) for r in others],
        ),
    )


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run: RunPath) -> RunResponse:
    """Get run by ID"""
    return RunResponse.model_validate(run)


@router.patch("/runs/{run_id}", response_model=RunResponse)
async def update_run(
    data: RunUpdate,
    run: RunPath,
    repo: RunRepo,
) -> RunResponse:
    """Update a run"""
    updated = await repo.update(run.run_id, data)
    if not updated:
        # This shouldn't happen since we already validated the run exists
        raise RuntimeError("Run update failed unexpectedly")
    return RunResponse.model_validate(updated)
