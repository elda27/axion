"""Run schemas"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RunStatus(str, Enum):
    """Run status enumeration"""

    ACTIVE = "active"
    GARBAGE = "garbage"
    ARCHIVED = "archived"


class RunCreate(BaseModel):
    """Schema for creating a run"""

    name: str = Field(..., min_length=1, max_length=255)
    status: RunStatus = RunStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    note: str | None = None


class RunUpdate(BaseModel):
    """Schema for updating a run"""

    name: str | None = Field(None, min_length=1, max_length=255)
    status: RunStatus | None = None
    tags: list[str] | None = None
    note: str | None = None


class RunResponse(BaseModel):
    """Schema for run response"""

    run_id: str = Field(..., alias="runId")
    batch_id: str = Field(..., alias="batchId")
    name: str
    status: RunStatus
    tags: list[str] = Field(default_factory=list)
    note: str | None = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> list[str]:
        """Parse tags from JSON string if needed"""
        if isinstance(v, str):
            return json.loads(v)
        return v


class RunBriefResponse(BaseModel):
    """Brief run response for summary views"""

    run_id: str = Field(..., alias="runId")
    name: str

    model_config = {"populate_by_name": True, "from_attributes": True}


class RecentCollapsed(BaseModel):
    """Recent runs collapsed section"""

    default_open: bool = Field(default=False, alias="defaultOpen")
    runs: list[RunBriefResponse]

    model_config = {"populate_by_name": True}


class OthersSection(BaseModel):
    """Others section with cursor pagination"""

    cursor: str | None = None
    runs: list[RunBriefResponse]


class RunSummaryResponse(BaseModel):
    """Run summary response with champion, recent, user_selected, and others"""

    champion: RunBriefResponse | None = None
    recent_collapsed: RecentCollapsed = Field(..., alias="recentCollapsed")
    user_selected: list[RunBriefResponse] = Field(
        default_factory=list, alias="userSelected"
    )
    others: OthersSection

    model_config = {"populate_by_name": True}
