"""Aggregation schemas"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AggregationCreate(BaseModel):
    """Schema for creating an aggregation"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    group_by_keys: list[str] = Field(
        default_factory=list,
        alias="groupByKeys",
        description="Metadata keys used for grouping runs (e.g. ['epoch', 'model_name'])",
    )
    filter: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata filter spec (e.g. {'model_name': ['gpt-4o', 'claude-3']})",
    )

    model_config = {"populate_by_name": True}


class AggregationResponse(BaseModel):
    """Schema for aggregation response"""

    aggregation_id: str = Field(..., alias="aggregationId")
    project_id: str = Field(..., alias="projectId")
    name: str
    description: str | None = None
    group_by_keys: list[str] = Field(default_factory=list, alias="groupByKeys")
    filter: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(..., alias="createdAt")
    member_count: int = Field(0, alias="memberCount")

    model_config = {"populate_by_name": True, "from_attributes": True}


class AggregationMemberAdd(BaseModel):
    """Schema for adding a run to an aggregation"""

    run_id: str = Field(..., alias="runId")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata values for this run in the aggregation context (e.g. {'epoch': 5})",
    )

    model_config = {"populate_by_name": True}


class AggregationMemberResponse(BaseModel):
    """Schema for aggregation member response"""

    member_id: str = Field(..., alias="memberId")
    aggregation_id: str = Field(..., alias="aggregationId")
    run_id: str = Field(..., alias="runId")
    metadata: dict[str, Any] = Field(default_factory=dict)
    added_at: datetime = Field(..., alias="addedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}
