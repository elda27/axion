"""Database migration helpers."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

PACKAGE_ROOT = Path(__file__).resolve().parents[4]
ALEMBIC_CONFIG_PATH = PACKAGE_ROOT / "alembic.ini"


def run_startup_migrations() -> None:
    """Apply all pending migrations before the server starts accepting requests."""
    config = Config(os.fspath(ALEMBIC_CONFIG_PATH))
    command.upgrade(config, "head")
