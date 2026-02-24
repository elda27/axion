from __future__ import annotations

import builtins
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from axion_lab.high_level import create_artifact, create_run, set_active_run


@dataclass
class _Named:
    name: str
    id_value: str

    @property
    def org_id(self) -> str:
        return self.id_value

    @property
    def project_id(self) -> str:
        return self.id_value

    @property
    def batch_id(self) -> str:
        return self.id_value


class _FakeOrgService:
    def __init__(self, items: builtins.list[_Named]) -> None:
        self._items = items

    def list(self, *, limit: int = 100, cursor: str | None = None):
        return SimpleNamespace(items=self._items, next_cursor=None)

    def create(self, name: str):
        item = _Named(name=name, id_value="org-created")
        self._items.append(item)
        return item


class _FakeProjectService:
    def __init__(self, items: builtins.list[_Named]) -> None:
        self._items = items

    def list(self, org_id: str, *, limit: int = 100, cursor: str | None = None):
        return SimpleNamespace(items=self._items, next_cursor=None)

    def create(self, org_id: str, name: str):
        item = _Named(name=name, id_value="project-created")
        self._items.append(item)
        return item


class _FakeBatchService:
    def __init__(self, items: builtins.list[_Named]) -> None:
        self._items = items

    def list(self, project_id: str, *, limit: int = 100, cursor: str | None = None):
        return SimpleNamespace(items=self._items, next_cursor=None)

    def create(self, project_id: str, name: str):
        item = _Named(name=name, id_value="batch-created")
        self._items.append(item)
        return item


class _FakeRunService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[str] | None, str | None]] = []

    def create(
        self,
        batch_id: str,
        name: str,
        *,
        tags: list[str] | None = None,
        note: str | None = None,
    ):
        self.calls.append((batch_id, name, tags, note))
        return SimpleNamespace(run_id="run-001", name=name)


class _FakeArtifactService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(
        self,
        run_id: str,
        *,
        kind: str,
        type: str,
        label: str,
        payload: object,
        meta: dict[str, object] | None = None,
    ):
        call = {
            "run_id": run_id,
            "kind": kind,
            "type": type,
            "label": label,
            "payload": payload,
            "meta": meta,
        }
        self.calls.append(call)
        return SimpleNamespace(artifact_id="art-001", **call)


class _FakeClient:
    def __init__(
        self,
        org_items: list[_Named],
        project_items: list[_Named],
        batch_items: list[_Named],
    ) -> None:
        self.orgs = _FakeOrgService(org_items)
        self.projects = _FakeProjectService(project_items)
        self.batches = _FakeBatchService(batch_items)
        self.runs = _FakeRunService()
        self.artifacts = _FakeArtifactService()


@pytest.fixture(autouse=True)
def _reset_active_run() -> None:
    set_active_run(None)


@pytest.fixture
def _env_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXION_LAB_ORG", "Org-A")
    monkeypatch.setenv("AXION_LAB_PROJECT", "Project-A")
    monkeypatch.setenv("AXION_LAB_BATCH", "Batch-A")


def test_create_run_uses_existing_context(_env_context: None) -> None:
    client = _FakeClient(
        org_items=[_Named(name="Org-A", id_value="org-1")],
        project_items=[_Named(name="Project-A", id_value="project-1")],
        batch_items=[_Named(name="Batch-A", id_value="batch-1")],
    )

    run = create_run("run-a", tags=["t1"], note="memo", client=client)  # type: ignore[arg-type]

    assert run.run_id == "run-001"
    assert client.runs.calls == [("batch-1", "run-a", ["t1"], "memo")]


def test_create_run_get_or_create_context(_env_context: None) -> None:
    client = _FakeClient(org_items=[], project_items=[], batch_items=[])

    run = create_run("run-b", client=client)  # type: ignore[arg-type]

    assert run.run_id == "run-001"
    assert client.runs.calls == [("batch-created", "run-b", None, None)]


def test_create_artifact_uses_active_run(_env_context: None) -> None:
    client = _FakeClient(
        org_items=[_Named(name="Org-A", id_value="org-1")],
        project_items=[_Named(name="Project-A", id_value="project-1")],
        batch_items=[_Named(name="Batch-A", id_value="batch-1")],
    )
    create_run("run-c", client=client)  # type: ignore[arg-type]

    artifact = create_artifact(
        kind="inline_number",
        type="evaluation",
        label="score",
        payload=0.9,
        client=client,  # type: ignore[arg-type]
    )

    assert artifact.run_id == "run-001"
    assert client.artifacts.calls[-1]["run_id"] == "run-001"


def test_create_artifact_requires_run_id_without_active_run(_env_context: None) -> None:
    client = _FakeClient(org_items=[], project_items=[], batch_items=[])

    with pytest.raises(ValueError, match="run_id is required"):
        create_artifact(
            kind="inline_text",
            type="note",
            label="memo",
            payload="hello",
            client=client,  # type: ignore[arg-type]
        )


def test_create_run_with_explicit_org_and_project(_env_context: None) -> None:
    """org / project kwargs override environment variables."""
    client = _FakeClient(
        org_items=[_Named(name="Custom-Org", id_value="org-custom")],
        project_items=[_Named(name="Custom-Project", id_value="project-custom")],
        batch_items=[_Named(name="Batch-A", id_value="batch-1")],
    )

    run = create_run(
        "run-d",
        org="Custom-Org",
        project="Custom-Project",
        client=client,  # type: ignore[arg-type]
    )

    assert run.run_id == "run-001"
    # The run should have been created using the custom org/project context
    assert client.runs.calls == [("batch-1", "run-d", None, None)]


def test_create_run_with_explicit_org_only(_env_context: None) -> None:
    """Only org kwarg overrides; project falls back to env var."""
    client = _FakeClient(
        org_items=[_Named(name="Override-Org", id_value="org-override")],
        project_items=[_Named(name="Project-A", id_value="project-1")],
        batch_items=[_Named(name="Batch-A", id_value="batch-1")],
    )

    run = create_run("run-e", org="Override-Org", client=client)  # type: ignore[arg-type]

    assert run.run_id == "run-001"
    assert client.runs.calls == [("batch-1", "run-e", None, None)]


def test_create_run_with_explicit_project_only(_env_context: None) -> None:
    """Only project kwarg overrides; org falls back to env var."""
    client = _FakeClient(
        org_items=[_Named(name="Org-A", id_value="org-1")],
        project_items=[_Named(name="Override-Project", id_value="project-override")],
        batch_items=[_Named(name="Batch-A", id_value="batch-1")],
    )

    run = create_run("run-f", project="Override-Project", client=client)  # type: ignore[arg-type]

    assert run.run_id == "run-001"
    assert client.runs.calls == [("batch-1", "run-f", None, None)]


def test_create_run_explicit_args_bypass_missing_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When org/project are passed explicitly, the env vars are not required."""
    monkeypatch.delenv("AXION_LAB_ORG", raising=False)
    monkeypatch.delenv("AXION_LAB_PROJECT", raising=False)
    monkeypatch.setenv("AXION_LAB_BATCH", "Batch-X")

    client = _FakeClient(
        org_items=[_Named(name="Arg-Org", id_value="org-arg")],
        project_items=[_Named(name="Arg-Project", id_value="project-arg")],
        batch_items=[_Named(name="Batch-X", id_value="batch-x")],
    )

    run = create_run(
        "run-g",
        org="Arg-Org",
        project="Arg-Project",
        client=client,  # type: ignore[arg-type]
    )

    assert run.run_id == "run-001"
    assert client.runs.calls == [("batch-x", "run-g", None, None)]


def test_create_run_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AXION_LAB_ORG", raising=False)
    monkeypatch.delenv("AXION_LAB_PROJECT", raising=False)
    monkeypatch.delenv("AXION_LAB_BATCH", raising=False)
    client = _FakeClient(org_items=[], project_items=[], batch_items=[])

    with pytest.raises(ValueError, match="Missing required environment variables"):
        create_run("run-z", client=client)  # type: ignore[arg-type]
