"""Quality Metric schemas"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class QualityMetricSource(str, Enum):
    """Quality Metric source enumeration"""

    RAW = "raw"
    DERIVED = "derived"
    MANUAL = "manual"


class QualityMetricResponse(BaseModel):
    """Schema for quality metric response"""

    qm_id: str = Field(..., alias="qmId")
    run_id: str = Field(..., alias="runId")
    key: str
    value: Any
    source: QualityMetricSource
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
