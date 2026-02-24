"""Tests for append_series / reset_series time-series helpers."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from axion_lab.api import _series_state
from axion_lab.high_level import append_series, reset_series, set_active_run

# ---------------------------------------------------------------------------
# Fake services (reused from test_high_level_api.py)
# ---------------------------------------------------------------------------


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


class _MinimalFakeClient:
    """Only exposes artifacts — sufficient for append_series."""

    def __init__(self) -> None:
        self.artifacts = _FakeArtifactService()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Reset module-level state between tests."""
    set_active_run(None)
    reset_series()


# ---------------------------------------------------------------------------
# Core behaviour
# ---------------------------------------------------------------------------


class TestAppendSeriesAutoStep:
    """Step auto-increment and wall-clock injection."""

    def test_auto_step_starts_at_zero(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=1.5,
            client=client,  # type: ignore[arg-type]
        )

        meta = result.meta
        assert meta["series_step"] == 0
        assert "series_wall" in meta
        assert meta["series_tag"] == "loss"

    def test_auto_step_increments(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        for expected_step in range(5):
            result = append_series(
                tag="loss",
                kind="inline_number",
                type="evaluation",
                payload=float(expected_step),
                client=client,  # type: ignore[arg-type]
            )
            assert result.meta["series_step"] == expected_step

    def test_different_tags_have_independent_counters(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.5, client=client)  # type: ignore[arg-type]
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.4, client=client)  # type: ignore[arg-type]

        result_acc = append_series(tag="accuracy", kind="inline_number", type="evaluation", payload=0.9, client=client)  # type: ignore[arg-type]
        assert result_acc.meta["series_step"] == 0  # independent counter

        result_loss = append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.3, client=client)  # type: ignore[arg-type]
        assert result_loss.meta["series_step"] == 2  # continues from earlier

    def test_different_runs_have_independent_counters(self) -> None:
        client = _MinimalFakeClient()

        set_active_run("run-A")
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=1.0, client=client)  # type: ignore[arg-type]
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.9, client=client)  # type: ignore[arg-type]

        set_active_run("run-B")
        result = append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.5, client=client)  # type: ignore[arg-type]
        assert result.meta["series_step"] == 0


class TestAppendSeriesExplicitStep:
    """Explicit step overrides auto-increment."""

    def test_explicit_step_is_honoured(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=0.7,
            step=42,
            client=client,  # type: ignore[arg-type]
        )
        assert result.meta["series_step"] == 42

    def test_explicit_step_does_not_affect_auto_counter(self) -> None:
        """After an explicit step, auto should continue from where it was."""
        set_active_run("run-1")
        client = _MinimalFakeClient()

        # auto: 0
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=1.0, client=client)  # type: ignore[arg-type]
        # explicit: 100 (should NOT move auto counter)
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.9, step=100, client=client)  # type: ignore[arg-type]
        # auto again: should be 1
        result = append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.8, client=client)  # type: ignore[arg-type]
        assert result.meta["series_step"] == 1


class TestAppendSeriesWall:
    """Wall-clock time behaviour."""

    def test_wall_defaults_to_current_time(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()
        before = time.time()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=0.5,
            client=client,  # type: ignore[arg-type]
        )

        after = time.time()
        assert before <= result.meta["series_wall"] <= after

    def test_explicit_wall_is_honoured(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=0.5,
            wall=1234567890.0,
            client=client,  # type: ignore[arg-type]
        )
        assert result.meta["series_wall"] == 1234567890.0


class TestAppendSeriesAllKinds:
    """All artifact kinds are supported, not just inline_number."""

    def test_inline_text(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="generated_text",
            kind="inline_text",
            type="note",
            payload="epoch 0 output",
            client=client,  # type: ignore[arg-type]
        )
        assert result.payload == "epoch 0 output"
        assert result.meta["series_step"] == 0

    def test_url(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="checkpoint_link",
            kind="url",
            type="object_storage",
            payload="s3://bucket/step-0/model.pt",
            client=client,  # type: ignore[arg-type]
        )
        assert result.kind == "url"
        assert result.meta["series_step"] == 0

    def test_inline_json(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="confusion_matrix",
            kind="inline_json",
            type="evaluation",
            payload={"tp": 10, "fp": 2, "fn": 1, "tn": 50},
            client=client,  # type: ignore[arg-type]
        )
        assert result.payload == {"tp": 10, "fp": 2, "fn": 1, "tn": 50}
        assert result.meta["series_step"] == 0


class TestAppendSeriesMeta:
    """User-supplied meta is merged, not overwritten."""

    def test_user_meta_preserved(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=0.5,
            meta={"lr": 0.001, "batch_size": 32},
            client=client,  # type: ignore[arg-type]
        )

        assert result.meta["lr"] == 0.001
        assert result.meta["batch_size"] == 32
        assert result.meta["series_step"] == 0
        assert "series_wall" in result.meta

    def test_user_meta_can_override_series_keys(self) -> None:
        """If user explicitly sets series_step in meta, it should be kept."""
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=0.5,
            meta={"series_step": 999},
            client=client,  # type: ignore[arg-type]
        )
        # setdefault preserves existing value
        assert result.meta["series_step"] == 999


class TestAppendSeriesLabel:
    """The artifact label is set to the tag."""

    def test_label_equals_tag(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        result = append_series(
            tag="train/loss",
            kind="inline_number",
            type="evaluation",
            payload=0.5,
            client=client,  # type: ignore[arg-type]
        )
        assert result.label == "train/loss"


class TestAppendSeriesRequiresRun:
    """Error when no run is available."""

    def test_raises_without_active_run(self) -> None:
        client = _MinimalFakeClient()

        with pytest.raises(ValueError, match="run_id is required"):
            append_series(
                tag="loss",
                kind="inline_number",
                type="evaluation",
                payload=0.5,
                client=client,  # type: ignore[arg-type]
            )

    def test_explicit_run_id_works_without_active(self) -> None:
        client = _MinimalFakeClient()

        result = append_series(
            tag="loss",
            kind="inline_number",
            type="evaluation",
            payload=0.5,
            run_id="explicit-run",
            client=client,  # type: ignore[arg-type]
        )
        assert result.run_id == "explicit-run"


class TestResetSeries:
    """reset_series clears step counters."""

    def test_reset_all(self) -> None:
        set_active_run("run-1")
        client = _MinimalFakeClient()

        append_series(tag="loss", kind="inline_number", type="evaluation", payload=1.0, client=client)  # type: ignore[arg-type]
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.9, client=client)  # type: ignore[arg-type]

        reset_series()

        result = append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.8, client=client)  # type: ignore[arg-type]
        assert result.meta["series_step"] == 0

    def test_reset_specific_run(self) -> None:
        client = _MinimalFakeClient()

        set_active_run("run-A")
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=1.0, client=client)  # type: ignore[arg-type]
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.9, client=client)  # type: ignore[arg-type]

        set_active_run("run-B")
        append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.5, client=client)  # type: ignore[arg-type]

        # Reset only run-A
        reset_series(run_id="run-A")

        # run-A counter is reset
        set_active_run("run-A")
        result_a = append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.7, client=client)  # type: ignore[arg-type]
        assert result_a.meta["series_step"] == 0

        # run-B counter is untouched
        set_active_run("run-B")
        result_b = append_series(tag="loss", kind="inline_number", type="evaluation", payload=0.4, client=client)  # type: ignore[arg-type]
        assert result_b.meta["series_step"] == 1


class TestSeriesStateThreadSafety:
    """Basic thread safety of _SeriesState."""

    def test_concurrent_increments(self) -> None:
        import threading

        state = _series_state
        reset_series()
        set_active_run("run-concurrent")

        results: list[int] = []
        lock = threading.Lock()

        def worker(n: int) -> None:
            for _ in range(n):
                step = state.next_step("run-concurrent", "metric")
                with lock:
                    results.append(step)

        threads = [threading.Thread(target=worker, args=(50,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 200 steps should be unique
        assert len(results) == 200
        assert len(set(results)) == 200
        assert sorted(results) == list(range(200))
