from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from axion_server.ops.dp.runner import DPRunner, RunScores
from axion_server.shared.domain import DPJobStatus, QualityMetricSource


def _run(*, run_id: str = "run-1"):
    return SimpleNamespace(run_id=run_id)


def _artifact(
    *, artifact_id: str = "art-1", type: str = "evaluation", kind: str = "inline_json"
):
    return SimpleNamespace(
        artifact_id=artifact_id,
        type=type,
        kind=kind,
        payload_text=None,
    )


class TestExtractScores:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_score_artifacts(self) -> None:
        run = _run()
        artifact_repo = Mock()
        artifact_repo.list_by_run = AsyncMock(return_value=([], None))

        result = await DPRunner._extract_scores(run, artifact_repo)

        assert result is None

    @pytest.mark.asyncio
    async def test_extracts_individual_case_scores(self) -> None:
        run = _run(run_id="run-1")
        art = _artifact()
        artifact_repo = Mock()
        artifact_repo.list_by_run = AsyncMock(return_value=([art], None))
        artifact_repo.get_payload = Mock(
            return_value={"case_id": "case-1", "score": 0.85}
        )

        result = await DPRunner._extract_scores(run, artifact_repo)

        assert result is not None
        assert result.run_id == "run-1"
        assert result.cases == {"case-1": 0.85}

    @pytest.mark.asyncio
    async def test_extracts_batch_format_scores(self) -> None:
        run = _run(run_id="run-2")
        art = _artifact()
        artifact_repo = Mock()
        artifact_repo.list_by_run = AsyncMock(return_value=([art], None))
        artifact_repo.get_payload = Mock(
            return_value={"scores": {"c1": 0.9, "c2": 0.8}}
        )

        result = await DPRunner._extract_scores(run, artifact_repo)

        assert result is not None
        assert result.cases == {"c1": 0.9, "c2": 0.8}

    @pytest.mark.asyncio
    async def test_handles_extraction_errors_gracefully(self) -> None:
        run = _run()
        art = _artifact()
        artifact_repo = Mock()
        artifact_repo.list_by_run = AsyncMock(return_value=([art], None))
        artifact_repo.get_payload = Mock(side_effect=Exception("parse error"))

        result = await DPRunner._extract_scores(run, artifact_repo)

        assert result is None


class TestComputeQM:
    @pytest.mark.asyncio
    async def test_computes_mean_min_max_count(self) -> None:
        run = _run(run_id="run-1")
        art = _artifact()
        artifact_repo = Mock()
        artifact_repo.list_by_run = AsyncMock(return_value=([art], None))
        artifact_repo.get_payload = Mock(
            return_value={"scores": {"c1": 0.8, "c2": 0.9, "c3": 1.0}}
        )

        qm_repo = Mock()
        qm_repo.upsert = AsyncMock()

        await DPRunner._compute_qm(run, artifact_repo, qm_repo)

        calls = qm_repo.upsert.await_args_list
        keys = [c.kwargs["key"] for c in calls]
        assert "mean_score" in keys
        assert "min_score" in keys
        assert "max_score" in keys
        assert "case_count" in keys

        mean_call = next(c for c in calls if c.kwargs["key"] == "mean_score")
        assert mean_call.kwargs["value"] == 0.9
        assert mean_call.kwargs["source"] == QualityMetricSource.DERIVED

    @pytest.mark.asyncio
    async def test_stores_raw_metrics(self) -> None:
        run = _run(run_id="run-1")
        metrics_art = _artifact(artifact_id="met-1", type="metrics", kind="metrics")
        artifact_repo = Mock()
        artifact_repo.list_by_run = AsyncMock(return_value=([metrics_art], None))
        artifact_repo.get_payload = Mock(
            return_value={"latency": 42, "throughput": 100.5}
        )

        qm_repo = Mock()
        qm_repo.upsert = AsyncMock()

        await DPRunner._compute_qm(run, artifact_repo, qm_repo)

        calls = qm_repo.upsert.await_args_list
        keys = [c.kwargs["key"] for c in calls]
        assert "latency" in keys
        assert "throughput" in keys

        latency_call = next(c for c in calls if c.kwargs["key"] == "latency")
        assert latency_call.kwargs["source"] == QualityMetricSource.RAW


class TestComputeCI:
    @pytest.mark.asyncio
    async def test_computes_delta_vs_champion(self) -> None:
        run_scores = RunScores(run_id="run-1", cases={"c1": 0.9, "c2": 0.8})
        champion_scores = RunScores(run_id="champ", cases={"c1": 0.7, "c2": 0.6})
        all_scores = [run_scores, champion_scores]

        ci_repo = Mock()
        ci_repo.upsert = AsyncMock()

        await DPRunner._compute_ci(run_scores, champion_scores, all_scores, ci_repo)

        calls = ci_repo.upsert.await_args_list
        keys = [c.kwargs["key"] for c in calls]
        assert "delta_vs_champion_mean" in keys
        assert "win_rate_vs_champion" in keys
        assert "rank_overall" in keys
        assert "is_candidate" in keys

        delta_call = next(
            c for c in calls if c.kwargs["key"] == "delta_vs_champion_mean"
        )
        assert delta_call.kwargs["value"] == 0.2
        assert delta_call.kwargs["baseline_ref"] == "champ"

        win_rate_call = next(
            c for c in calls if c.kwargs["key"] == "win_rate_vs_champion"
        )
        assert win_rate_call.kwargs["value"] == 1.0

    @pytest.mark.asyncio
    async def test_skip_champion_comparison_when_same_run(self) -> None:
        run_scores = RunScores(run_id="run-1", cases={"c1": 0.9})
        champion_scores = RunScores(run_id="run-1", cases={"c1": 0.9})
        all_scores = [run_scores]

        ci_repo = Mock()
        ci_repo.upsert = AsyncMock()

        await DPRunner._compute_ci(run_scores, champion_scores, all_scores, ci_repo)

        keys = [c.kwargs["key"] for c in ci_repo.upsert.await_args_list]
        assert "delta_vs_champion_mean" not in keys
        assert "win_rate_vs_champion" not in keys

    @pytest.mark.asyncio
    async def test_skip_champion_comparison_when_none(self) -> None:
        run_scores = RunScores(run_id="run-1", cases={"c1": 0.9})
        all_scores = [run_scores]

        ci_repo = Mock()
        ci_repo.upsert = AsyncMock()

        await DPRunner._compute_ci(run_scores, None, all_scores, ci_repo)

        keys = [c.kwargs["key"] for c in ci_repo.upsert.await_args_list]
        assert "delta_vs_champion_mean" not in keys
        assert "rank_overall" in keys

    @pytest.mark.asyncio
    async def test_ranking(self) -> None:
        scores_1 = RunScores(run_id="run-1", cases={"c1": 0.5})
        scores_2 = RunScores(run_id="run-2", cases={"c1": 0.9})
        scores_3 = RunScores(run_id="run-3", cases={"c1": 0.7})
        all_scores = [scores_1, scores_2, scores_3]

        ci_repo = Mock()
        ci_repo.upsert = AsyncMock()

        await DPRunner._compute_ci(scores_1, None, all_scores, ci_repo)

        rank_call = next(
            c
            for c in ci_repo.upsert.await_args_list
            if c.kwargs["key"] == "rank_overall"
        )
        assert rank_call.kwargs["value"] == 3

    @pytest.mark.asyncio
    async def test_skip_empty_scores(self) -> None:
        run_scores = RunScores(run_id="run-1", cases={})

        ci_repo = Mock()
        ci_repo.upsert = AsyncMock()

        await DPRunner._compute_ci(run_scores, None, [run_scores], ci_repo)

        ci_repo.upsert.assert_not_awaited()
