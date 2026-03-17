import os
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import axion_lab.cli as cli


def test_run_alembic_upgrade_uses_packaged_script_location(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_upgrade(config, revision: str) -> None:
        captured["revision"] = revision
        captured["script_location"] = config.get_main_option("script_location")

    monkeypatch.setattr(cli.command, "upgrade", fake_upgrade)

    return_code = cli.run_alembic(["upgrade", "head"], exit_after=False)

    expected_script_location = (
        Path(cli.__file__).resolve().parents[1] / "axion_lab_alembic"
    )
    script_location = captured["script_location"]

    assert return_code == 0
    assert captured["revision"] == "head"
    assert isinstance(script_location, str)
    assert Path(script_location).resolve() == expected_script_location


def test_run_alembic_revision_supports_autogenerate(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_revision(config, *, message: str, autogenerate: bool) -> None:
        captured["message"] = message
        captured["autogenerate"] = autogenerate
        captured["script_location"] = config.get_main_option("script_location")

    monkeypatch.setattr(cli.command, "revision", fake_revision)

    return_code = cli.run_alembic(
        ["revision", "-m", "add runs table", "--autogenerate"],
        exit_after=False,
    )

    expected_script_location = (
        Path(cli.__file__).resolve().parents[1] / "axion_lab_alembic"
    )
    script_location = captured["script_location"]

    assert return_code == 0
    assert captured["message"] == "add runs table"
    assert captured["autogenerate"] is True
    assert isinstance(script_location, str)
    assert Path(script_location).resolve() == expected_script_location


def test_run_server_applies_local_defaults(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_uvicorn_run(app: str, *, host: str, port: int, reload: bool) -> None:
        captured["uvicorn_app"] = app
        captured["uvicorn_host"] = host
        captured["uvicorn_port"] = port
        captured["uvicorn_reload"] = reload

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_uvicorn_run))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_TYPE", raising=False)
    monkeypatch.delenv("OBJECT_STORE_PROVIDER", raising=False)
    monkeypatch.delenv("OBJECT_STORE_LOCAL_PATH", raising=False)

    cli.run_server("127.0.0.1", 8123, True)

    assert os.environ["DATABASE_URL"] == "sqlite+aiosqlite:///./axion_lab.db"
    assert os.environ["DATABASE_TYPE"] == "sqlite"
    assert os.environ["OBJECT_STORE_PROVIDER"] == "file"
    assert os.environ["OBJECT_STORE_LOCAL_PATH"] == "./data/object_store"
    assert captured["uvicorn_app"] == "axion_lab_server.apps.api.app:app"
    assert captured["uvicorn_host"] == "127.0.0.1"
    assert captured["uvicorn_port"] == 8123
    assert captured["uvicorn_reload"] is True


def test_python_module_entrypoint_delegates_to_cli(monkeypatch) -> None:
    called = False

    def fake_main() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("axion_lab.cli.main", fake_main)

    runpy.run_module("axion_lab.__main__", run_name="__main__")

    assert called is True
