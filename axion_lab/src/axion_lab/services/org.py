"""Organization service."""

from __future__ import annotations

from axion_lab.schemas import CursorPaginatedResponse, OrgCreate, OrgResponse
from axion_lab.services._http import HttpTransport


class OrgService:
    """CRUD operations for organizations."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def create(self, name: str) -> OrgResponse:
        """Create a new organization."""
        data = self._http.post("/orgs", json=OrgCreate(name=name).model_dump())
        return OrgResponse.model_validate(data)

    def list(
        self,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[OrgResponse]:
        """List organizations with cursor pagination."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get("/orgs", params=params)
        return CursorPaginatedResponse[OrgResponse].model_validate(data)

    def get(self, org_id: str) -> OrgResponse:
        """Get an organization by ID."""
        data = self._http.get(f"/orgs/{org_id}")
        return OrgResponse.model_validate(data)
