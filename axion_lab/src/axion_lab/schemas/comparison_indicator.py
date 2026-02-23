"""Comparison Indicator schemas"""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ComparisonIndicatorResponse(BaseModel):
    """Schema for comparison indicator response"""

    ci_id: str = Field(..., alias="ciId")
    run_id: str = Field(..., alias="runId")
    key: str
    value: Any
    baseline_ref: str | None = Field(None, alias="baselineRef")
    computed_at: datetime = Field(..., alias="computedAt")
    version: int

    model_config = {"populate_by_name": True, "from_attributes": True}

    @field_validator("value", mode="before")
    @classmethod
    def parse_value(cls, v: Any) -> Any:
        """Parse value from JSON string if needed"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v
