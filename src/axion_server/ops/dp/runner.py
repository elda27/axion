"""DP Runner - computes Quality Metrics and Comparison Indicators"""

import logging
from dataclasses import dataclass
from statistics import mean
from typing import Any

from axion_server.gateways.storage import get_object_store
from axion_server.repos import (
    ArtifactRepository,
    ComparisonIndicatorRepository,
    DPJobRepository,
    QualityMetricRepository,
    RunPinRepository,
    RunRepository,
)
from axion_server.repos.models.entities import Artifact, Run
from axion_server.shared.domain import (
    DPJobMode,
    DPJobStatus,
    QualityMetricSource,
)
from axion_server.shared.kernel import get_session

logger = logging.getLogger(__name__)


@dataclass
class CaseScore:
    """Score for a single case within a run"""

    case_id: str
    score: float


@dataclass
class RunScores:
    """All case scores for a run"""

    run_id: str
    cases: dict[str, float]  # case_id -> score


class DPRunner:
    """Runner for DP jobs (Quality Metrics and Comparison Indicators)"""

    @staticmethod
    async def run_job(job_id: str) -> None:
        """Execute a DP job"""
        async with get_session() as session:
            job_repo = DPJobRepository(session)
            run_repo = RunRepository(session)
            artifact_repo = ArtifactRepository(session)
            qm_repo = QualityMetricRepository(session)
            ci_repo = ComparisonIndicatorRepository(session)
            pin_repo = RunPinRepository(session)

            # Get the job
            job = await job_repo.get(job_id)
            if not job:
                logger.error(f"Job not found: {job_id}")
                return

            # Mark as running
            await job_repo.update(job_id, status=DPJobStatus.RUNNING)

            try:
                # Get the run
                run = await run_repo.get(job.run_id)
                if not run:
                    raise ValueError(f"Run not found: {job.run_id}")

                # Get all runs in the batch for comparison
                all_runs = await run_repo.list_by_batch(
                    run.batch_id, limit=1000, offset=0
                )

                # Get champion run if exists
                champion_run: Run | None = None
                champion_pin = await pin_repo.get_by_batch_and_kind(
                    run.batch_id, "champion"
                )
                if champion_pin:
                    champion_run = await run_repo.get(champion_pin.run_id)

                # Compute based on mode
                if job.mode in (DPJobMode.FULL, DPJobMode.QM_ONLY):
                    await DPRunner._compute_qm(run, artifact_repo, qm_repo)

                if job.mode in (DPJobMode.FULL, DPJobMode.CI_ONLY):
                    # Get scores for all runs
                    all_run_scores: list[RunScores] = []
                    for r in all_runs:
                        scores = await DPRunner._extract_scores(r, artifact_repo)
                        if scores:
                            all_run_scores.append(scores)

                    # Get current run scores
                    run_scores = next(
                        (rs for rs in all_run_scores if rs.run_id == run.id),
                        None,
                    )

                    # Get champion scores
                    champion_scores: RunScores | None = None
                    if champion_run:
                        champion_scores = next(
                            (
                                rs
                                for rs in all_run_scores
                                if rs.run_id == champion_run.id
                            ),
                            None,
                        )

                    if run_scores:
                        await DPRunner._compute_ci(
                            run_scores,
                            champion_scores,
                            all_run_scores,
                            [r.id for r in all_runs],
                            ci_repo,
                        )

                # Mark as complete
                await job_repo.update(job_id, status=DPJobStatus.COMPLETED)
                logger.info(f"DP job completed: {job_id}")

            except Exception as e:
                logger.exception(f"DP job failed: {job_id}")
                await job_repo.update(
                    job_id,
                    status=DPJobStatus.FAILED,
                    error_message=str(e),
                )

    @staticmethod
    async def _extract_scores(
        run: Run,
        artifact_repo: ArtifactRepository,
    ) -> RunScores | None:
        """Extract scores from run artifacts"""
        # Get score artifacts
        artifacts = await artifact_repo.list_by_run(run.id, limit=100, offset=0)
        score_artifacts = [a for a in artifacts if a.kind == "score"]

        if not score_artifacts:
            return None

        cases: dict[str, float] = {}
        for artifact in score_artifacts:
            try:
                payload = await DPRunner._get_artifact_payload_async(
                    artifact, artifact_repo
                )
                if payload and isinstance(payload, dict):
                    if "case_id" in payload and "score" in payload:
                        cases[payload["case_id"]] = float(payload["score"])
                    elif "scores" in payload and isinstance(payload["scores"], dict):
                        # Batch format: {"scores": {"case1": 0.8, "case2": 0.9}}
                        for case_id, score in payload["scores"].items():
                            cases[case_id] = float(score)
            except Exception as e:
                logger.warning(
                    f"Failed to extract score from artifact {artifact.id}: {e}"
                )

        return RunScores(run_id=run.id, cases=cases) if cases else None

    @staticmethod
    async def _extract_raw_metrics(
        run: Run,
        artifact_repo: ArtifactRepository,
    ) -> dict[str, Any]:
        """Extract raw metrics from run artifacts"""
        artifacts = await artifact_repo.list_by_run(run.id, limit=100, offset=0)
        metrics_artifacts = [a for a in artifacts if a.kind == "metrics"]

        raw_metrics: dict[str, Any] = {}
        for artifact in metrics_artifacts:
            try:
                payload = await DPRunner._get_artifact_payload_async(
                    artifact, artifact_repo
                )
                if payload and isinstance(payload, dict):
                    raw_metrics.update(payload)
            except Exception as e:
                logger.warning(
                    f"Failed to extract metrics from artifact {artifact.id}: {e}"
                )

        return raw_metrics

    @staticmethod
    async def _compute_qm(
        run: Run,
        artifact_repo: ArtifactRepository,
        qm_repo: QualityMetricRepository,
    ) -> None:
        """Compute Quality Metrics for a run"""
        # Extract scores
        run_scores = await DPRunner._extract_scores(run, artifact_repo)

        if run_scores and run_scores.cases:
            scores = list(run_scores.cases.values())

            # Mean score
            mean_score = mean(scores)
            await qm_repo.upsert(
                run_id=run.id,
                key="mean_score",
                source=QualityMetricSource.SYSTEM,
                value=round(mean_score, 6),
            )

            # Min/max scores
            await qm_repo.upsert(
                run_id=run.id,
                key="min_score",
                source=QualityMetricSource.SYSTEM,
                value=round(min(scores), 6),
            )
            await qm_repo.upsert(
                run_id=run.id,
                key="max_score",
                source=QualityMetricSource.SYSTEM,
                value=round(max(scores), 6),
            )

            # Case count
            await qm_repo.upsert(
                run_id=run.id,
                key="case_count",
                source=QualityMetricSource.SYSTEM,
                value=len(scores),
            )

        # Extract and store raw metrics
        raw_metrics = await DPRunner._extract_raw_metrics(run, artifact_repo)
        for key, value in raw_metrics.items():
            if isinstance(value, (int, float, bool)):
                await qm_repo.upsert(
                    run_id=run.id,
                    key=key,
                    source=QualityMetricSource.RAW,
                    value=value,
                )

    @staticmethod
    async def _compute_ci(
        run_scores: RunScores,
        champion_scores: RunScores | None,
        all_run_scores: list[RunScores],
        all_run_ids: list[str],
        ci_repo: ComparisonIndicatorRepository,
    ) -> None:
        """Compute Comparison Indicators for a run"""
        scores = list(run_scores.cases.values())
        if not scores:
            return

        run_mean = mean(scores)

        # Comparison vs champion
        if champion_scores and champion_scores.run_id != run_scores.run_id:
            champion_scores_list = list(champion_scores.cases.values())
            if champion_scores_list:
                champion_mean = mean(champion_scores_list)

                # Delta vs champion (mean)
                delta = run_mean - champion_mean
                await ci_repo.upsert(
                    run_id=run_scores.run_id,
                    key="delta_vs_champion_mean",
                    value=round(delta, 6),
                    baseline_ref=champion_scores.run_id,
                )

                # Win rate vs champion (case-level)
                common_cases = set(run_scores.cases.keys()) & set(
                    champion_scores.cases.keys()
                )
                if common_cases:
                    wins = sum(
                        1
                        for c in common_cases
                        if run_scores.cases[c] > champion_scores.cases[c]
                    )
                    win_rate = wins / len(common_cases)
                    await ci_repo.upsert(
                        run_id=run_scores.run_id,
                        key="win_rate_vs_champion",
                        value=round(win_rate, 6),
                        baseline_ref=champion_scores.run_id,
                    )

        # Ranking among all runs
        all_means = []
        for rs in all_run_scores:
            rs_scores = list(rs.cases.values())
            if rs_scores:
                all_means.append((rs.run_id, mean(rs_scores)))

        # Sort by mean score descending
        all_means.sort(key=lambda x: x[1], reverse=True)
        rank = next(
            (i + 1 for i, (rid, _) in enumerate(all_means) if rid == run_scores.run_id),
            None,
        )

        if rank:
            await ci_repo.upsert(
                run_id=run_scores.run_id,
                key="rank_overall",
                value=rank,
            )

            # Is candidate (top 3 and not too far from best)
            is_candidate = rank <= 3
            if all_means:
                best_mean = all_means[0][1]
                if run_mean < best_mean - 0.1:  # Within 0.1 of best
                    is_candidate = False

            await ci_repo.upsert(
                run_id=run_scores.run_id,
                key="is_candidate",
                value=is_candidate,
            )

    @staticmethod
    def _get_artifact_payload(
        artifact: Artifact,
        artifact_repo: ArtifactRepository,
    ) -> Any:
        """Get artifact payload"""
        return artifact_repo.get_payload(artifact)

    @staticmethod
    async def _get_artifact_payload_async(
        artifact: Artifact,
        artifact_repo: ArtifactRepository,
    ) -> Any:
        """Get artifact payload (async version for object storage)"""
        # First try inline payload
        payload = artifact_repo.get_payload(artifact)
        if payload is not None:
            return payload

        # Try object storage
        if artifact.payload_text:
            return await DPRunner._fetch_object_storage_payload(artifact)

        return None

    @staticmethod
    async def _fetch_object_storage_payload(
        artifact: Artifact,
    ) -> Any:
        """Fetch payload from object storage"""
        try:
            object_store = get_object_store()
            key = artifact.payload_text
            if key:
                return await object_store.get_json(key)
        except Exception as e:
            logger.warning(f"Failed to fetch from object storage: {e}")
        return None
