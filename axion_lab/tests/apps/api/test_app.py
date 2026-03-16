import importlib
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from axion_lab_server.shared.libs.config import get_settings

app_module = importlib.import_module("axion_lab_server.apps.api.app")


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_create_app_registers_api_alias_routes() -> None:
    app = app_module.create_app(run_migrations_on_startup=False)

    route_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}

    assert "/v1/orgs" in route_paths
    assert "/api/v1/orgs" in route_paths


def test_create_app_serves_built_ui(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui_dist_dir = tmp_path / "dist"
    assets_dir = ui_dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    index_html = "<html><body><div id='root'>Axion Lab</div></body></html>"
    (ui_dist_dir / "index.html").write_text(index_html, encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('axion')", encoding="utf-8")
    monkeypatch.setenv("UI_DIST_DIR", str(ui_dist_dir))

    with TestClient(app_module.create_app(run_migrations_on_startup=False)) as client:
        assert client.get("/").status_code == 200
        assert client.get("/").text == index_html
        assert client.get("/orgs").status_code == 200
        assert client.get("/orgs").text == index_html
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/assets/app.js").text == "console.log('axion')"


def test_create_app_keeps_api_paths_out_of_spa_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui_dist_dir = tmp_path / "dist"
    ui_dist_dir.mkdir(parents=True)
    (ui_dist_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setenv("UI_DIST_DIR", str(ui_dist_dir))

    with TestClient(app_module.create_app(run_migrations_on_startup=False)) as client:
        assert client.get("/v1/does-not-exist").status_code == 404
        assert client.get("/api/v1/does-not-exist").status_code == 404
        assert client.get("/missing.css").status_code == 404


def test_create_app_runs_startup_migrations(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_run_startup_migrations() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        app_module, "run_startup_migrations", fake_run_startup_migrations
    )

    with TestClient(app_module.create_app()):
        pass

    assert called is True
