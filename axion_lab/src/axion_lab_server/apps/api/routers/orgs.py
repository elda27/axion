"""Organization API router"""

from fastapi import APIRouter, status

from axion_lab_server.apps.api.deps import OrgPath, OrgRepo
from axion_lab_server.shared.domain import CursorPaginatedResponse, OrgCreate, OrgResponse

router = APIRouter(prefix="/orgs", tags=["Organizations"])


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(data: OrgCreate, repo: OrgRepo) -> OrgResponse:
    """Create a new organization"""
    org = await repo.create(data)
    return OrgResponse.model_validate(org)


@router.get("", response_model=CursorPaginatedResponse[OrgResponse])
async def list_orgs(
    repo: OrgRepo,
    limit: int = 20,
    cursor: str | None = None,
) -> CursorPaginatedResponse[OrgResponse]:
    """List all organizations with cursor pagination"""
    orgs, next_cursor = await repo.list_all(limit=limit, cursor=cursor)
    return CursorPaginatedResponse(
        items=[OrgResponse.model_validate(o) for o in orgs],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(org: OrgPath) -> OrgResponse:
    """Get organization by ID"""
    return OrgResponse.model_validate(org)
