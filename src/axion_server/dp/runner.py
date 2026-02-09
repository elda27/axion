"""Embedded DP Runner for computing Quality Metrics and Comparison Indicators"""

import logging
import traceback
from dataclasses import dataclass
from statistics import mean, median
from typing import Any

from axion.schemas import DPJobMode, DPJobStatus, QualityMetricSource
from axion_server.database import get_session
from axion_server.models.entities import Artifact, Run
from axion_server.repositories import (
    ArtifactRepository,
    ComparisonIndicatorRepository,
    DPJobRepository,
    QualityMetricRepository,
    RunPinRepository,
    RunRepository,
)
from axion_server.storage import get_object_store

logger = logging.getLogger(__name__)


@dataclass
class CaseScore:
    """Single case score"""

    case_id: str
    score: float


@dataclass
class RunScores:
    """Scores for a single run"""

    run_id: str
    cases: dict[str, float]  # case_id -> score


class DPRunner:
    """Embedded DP Runner for computing metrics"""

    @staticmethod
    async def run_job(
        job_id: str,
        batch_id: str,
        mode: DPJobMode,
        recompute: bool,
    ) -> None:
        """Run a DP computation job"""
        async with get_session() as session:
            job_repo = DPJobRepository(session)
            run_repo = RunRepository(session)
            artifact_repo = ArtifactRepository(session)
            qm_repo = QualityMetricRepository(session)
            ci_repo = ComparisonIndicatorRepository(session)
            pin_repo = RunPinRepository(session)

            try:
                # Update job status to running
                await job_repo.update_status(job_id, DPJobStatus.RUNNING)
                await session.commit()

                # Fetch active runs
                include_garbage = mode == DPJobMode.INCLUDE_GARBAGE
                runs = await run_repo.list_active_for_dp(batch_id, include_garbage)

                if not runs:
                    logger.info(f"No runs to process for batch {batch_id}")
                    await job_repo.update_status(job_id, DPJobStatus.SUCCEEDED)
                    await session.commit()
                    return

                # Load artifacts and build case matrix
                run_scores_list: list[RunScores] = []

                for run in runs:
                    scores = await DPRunner._extract_scores(run, artifact_repo)
                    if scores:
                        run_scores_list.append(scores)

                    # Extract raw metrics from artifacts
                    await DPRunner._extract_raw_metrics(run, artifact_repo, qm_repo)

                # Compute Quality Metrics (derived)
                for run_scores in run_scores_list:
                    await DPRunner._compute_qm(run_scores, qm_repo)

                # Get champion for comparison
                champion_run_id = await pin_repo.get_champion_run_id(batch_id)
                champion_scores: RunScores | None = None
                if champion_run_id:
                    for rs in run_scores_list:
                        if rs.run_id == champion_run_id:
                            champion_scores = rs
                            break

                # Compute Comparison Indicators
                all_run_ids = [rs.run_id for rs in run_scores_list]
                for run_scores in run_scores_list:
                    await DPRunner._compute_ci(
                        run_scores,
                        champion_scores,
                        run_scores_list,
                        all_run_ids,
                        ci_repo,
                    )

                # Mark job as succeeded
                await job_repo.update_status(job_id, DPJobStatus.SUCCEEDED)
                await session.commit()

                logger.info(f"DP job {job_id} completed successfully")

            except Exception as e:
                logger.error(f"DP job {job_id} failed: {e}")
                logger.error(traceback.format_exc())

                # Mark job as failed
                await job_repo.update_status(
                    job_id, DPJobStatus.FAILED, error_text=str(e)
                )
                await session.commit()

    @staticmethod
    async def _extract_scores(
        run: Run,
        artifact_repo: ArtifactRepository,
    ) -> RunScores | None:
        """Extract case scores from run artifacts"""
        # Look for evaluation artifacts
        artifacts = await artifact_repo.list_by_run_and_type(run.run_id, "evaluation")

        cases: dict[str, float] = {}

        for artifact in artifacts:
            try:
                payload = DPRunner._get_artifact_payload(artifact, artifact_repo)

                if isinstance(payload, dict):
                    schema = payload.get("schema", "")

                    # Handle case_score_v1 schema
                    if schema == "case_score_v1" or "cases" in payload:
                        for case in payload.get("cases", []):
                            case_id = case.get("case_id") or case.get("id")
                            score = case.get("score")
                            if case_id and score is not None:
                                cases[str(case_id)] = float(score)

            except Exception as e:
                logger.warning(
                    f"Failed to extract scores from artifact {artifact.artifact_id}: {e}"
                )

        if not cases:
            return None

        return RunScores(run_id=run.run_id, cases=cases)

    @staticmethod
    async def _extract_raw_metrics(
        run: Run,
        artifact_repo: ArtifactRepository,
        qm_repo: QualityMetricRepository,
    ) -> None:
        """Extract raw metrics from inline artifacts"""
        # Get all artifacts for the run
        artifacts, _ = await artifact_repo.list_by_run(run.run_id, limit=1000)

        for artifact in artifacts:
            # Handle inline_number artifacts as raw metrics
            if artifact.kind == "inline_number" and artifact.payload_number is not None:
                await qm_repo.upsert(
                    run_id=run.run_id,
                    key=artifact.type,
                    value=artifact.payload_number,
                    source=QualityMetricSource.RAW,
                )

    @staticmethod
    async def _compute_qm(
        run_scores: RunScores,
        qm_repo: QualityMetricRepository,
    ) -> None:
        """Compute Quality Metrics for a run"""
        scores = list(run_scores.cases.values())

        if not scores:
            return

        # Mean score
        mean_score = mean(scores)
        await qm_repo.upsert(
            run_id=run_scores.run_id,
            key="mean_case_score",
            value=round(mean_score, 6),
            source=QualityMetricSource.DERIVED,
        )

        # Median score
        median_score = median(scores)
        await qm_repo.upsert(
            run_id=run_scores.run_id,
            key="median_case_score",
            value=round(median_score, 6),
            source=QualityMetricSource.DERIVED,
        )

        # Case count
        await qm_repo.upsert(
            run_id=run_scores.run_id,
            key="case_count",
            value=len(scores),
            source=QualityMetricSource.DERIVED,
        )

        # Failure rate (score < 0.5)
        failures = sum(1 for s in scores if s < 0.5)
        failure_rate = failures / len(scores)
        await qm_repo.upsert(
            run_id=run_scores.run_id,
            key="failure_rate",
            value=round(failure_rate, 6),
            source=QualityMetricSource.DERIVED,
        )

        # Min and max
        await qm_repo.upsert(
            run_id=run_scores.run_id,
            key="min_case_score",
            value=round(min(scores), 6),
            source=QualityMetricSource.DERIVED,
        )
        await qm_repo.upsert(
            run_id=run_scores.run_id,
            key="max_case_score",
            value=round(max(scores), 6),
            source=QualityMetricSource.DERIVED,
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
