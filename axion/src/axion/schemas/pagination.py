"""Pagination schemas"""

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters"""

    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


class CursorPaginatedResponse[T](BaseModel):
    """Cursor-based paginated response"""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
