"""Utility functions"""

from datetime import UTC, datetime

from ulid import ULID


def generate_id() -> str:
    """Generate a new ULID-based ID"""
    return str(ULID())


def utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(UTC)
