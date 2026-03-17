from pathlib import Path
from typing import cast

from axion_lab_server.shared.kernel import migrations


def test_create_alembic_config_uses_packaged_script_location() -> None:
    config = migrations.create_alembic_config()

    expected_script_location = (
        Path(migrations.__file__).resolve().parents[3] / "axion_lab_alembic"
    )
    script_location = cast(str, config.get_main_option("script_location"))

    assert Path(script_location).resolve() == expected_script_location


def test_run_startup_migrations_upgrades_head(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_upgrade(config, revision: str) -> None:
        captured["revision"] = revision
        captured["script_location"] = config.get_main_option("script_location")

    monkeypatch.setattr(migrations.command, "upgrade", fake_upgrade)

    migrations.run_startup_migrations()

    expected_script_location = (
        Path(migrations.__file__).resolve().parents[3] / "axion_lab_alembic"
    )
    script_location = cast(str, captured["script_location"])

    assert captured["revision"] == "head"
    assert Path(script_location).resolve() == expected_script_location
