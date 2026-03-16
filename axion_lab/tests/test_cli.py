import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import axion_lab.cli as cli


def test_run_alembic_uses_packaged_config(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, *, check: bool) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["check"] = check
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    return_code = cli.run_alembic(["upgrade", "head"], exit_after=False)

    package_root = Path(cli.__file__).resolve().parents[2]
    assert return_code == 0
    assert captured["command"] == [
        "alembic",
        "-c",
        os.fspath(package_root / "alembic.ini"),
        "upgrade",
        "head",
    ]
    assert captured["check"] is False


def test_run_alembic_does_not_override_current_working_directory(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    return_code = cli.run_alembic(["upgrade", "head"], exit_after=False)

    assert return_code == 0
    assert "cwd" not in cast(dict[str, object], captured["kwargs"])


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
