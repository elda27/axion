"""Database migration helpers."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

ALEMBIC_SCRIPT_LOCATION = Path(__file__).resolve().parents[3] / "axion_lab_alembic"


def create_alembic_config() -> Config:
    """Build an Alembic config that works from source and installed wheels."""
    if not ALEMBIC_SCRIPT_LOCATION.is_dir():
        raise FileNotFoundError(
            f"Alembic script location not found: {ALEMBIC_SCRIPT_LOCATION}"
        )

    config = Config()
    config.set_main_option("script_location", os.fspath(ALEMBIC_SCRIPT_LOCATION))
    return config


def run_startup_migrations() -> None:
    """Apply all pending migrations before the server starts accepting requests."""
    config = create_alembic_config()
    command.upgrade(config, "head")
