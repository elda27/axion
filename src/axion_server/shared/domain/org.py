"""Org schemas"""

from datetime import datetime

from pydantic import BaseModel, Field


class OrgCreate(BaseModel):
    """Schema for creating an organization"""

    name: str = Field(..., min_length=1, max_length=255)


class OrgResponse(BaseModel):
    """Schema for organization response"""

    org_id: str = Field(..., alias="orgId")
    name: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True, "from_attributes": True}
