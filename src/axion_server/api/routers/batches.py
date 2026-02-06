"""Batch API router"""

from fastapi import APIRouter, status

from axion_server.api.deps import BatchPath, BatchRepo, ProjectPath
from axion.schemas import BatchCreate, BatchResponse, CursorPaginatedResponse

router = APIRouter(tags=["Batches"])


@router.post(
    "/projects/{project_id}/batches",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_batch(
    data: BatchCreate,
    project: ProjectPath,
    repo: BatchRepo,
) -> BatchResponse:
    """Create a new batch in a project"""
    batch = await repo.create(project.project_id, data)
    return BatchResponse.model_validate(batch)


@router.get(
    "/projects/{project_id}/batches",
    response_model=CursorPaginatedResponse[BatchResponse],
)
async def list_batches(
    project: ProjectPath,
    repo: BatchRepo,
    limit: int = 20,
    cursor: str | None = None,
) -> CursorPaginatedResponse[BatchResponse]:
    """List batches in a project"""
    batches, next_cursor = await repo.list_by_project(
        project.project_id, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[BatchResponse.model_validate(b) for b in batches],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(batch: BatchPath) -> BatchResponse:
    """Get batch by ID"""
    return BatchResponse.model_validate(batch)
