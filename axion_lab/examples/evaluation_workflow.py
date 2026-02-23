#!/usr/bin/env python3
"""Axion Lab 評価ワークフロー: 複数 Run のスコア比較と DP 計算.

複数の Run を作成し、それぞれにスコア Artifact を登録した後、
DP（差分再計算）ジョブを実行して品質指標 (Quality Metric) と
比較指標 (Comparison Indicator) を自動算出するフローを示します。

Usage:
    uv run python examples/evaluation_workflow.py
"""

from __future__ import annotations

import time
from typing import TypedDict

from axion_lab import AxionLabClient


class _RunConfig(TypedDict):
    name: str
    tags: list[str]
    note: str
    scores: dict[str, int | float]


# ── シナリオデータ ───────────────────────────────────────────────
# 3つの異なるモデル/プロンプト設定で要約タスクを評価するシナリオ
RUN_CONFIGS: list[_RunConfig] = [
    {
        "name": "run-gpt4o-prompt-v1",
        "tags": ["gpt-4o", "prompt-v1"],
        "note": "GPT-4o with baseline prompt",
        "scores": {
            "rouge-l": 0.847,
            "bleu": 0.654,
            "bertscore": 0.891,
            "latency_p95_ms": 1250,
            "cost_usd": 4.32,
        },
    },
    {
        "name": "run-gpt4o-prompt-v2",
        "tags": ["gpt-4o", "prompt-v2"],
        "note": "GPT-4o with improved few-shot prompt",
        "scores": {
            "rouge-l": 0.892,
            "bleu": 0.721,
            "bertscore": 0.923,
            "latency_p95_ms": 1380,
            "cost_usd": 5.10,
        },
    },
    {
        "name": "run-claude-sonnet-prompt-v2",
        "tags": ["claude-sonnet", "prompt-v2"],
        "note": "Claude Sonnet with improved few-shot prompt",
        "scores": {
            "rouge-l": 0.876,
            "bleu": 0.698,
            "bertscore": 0.915,
            "latency_p95_ms": 980,
            "cost_usd": 3.85,
        },
    },
]


def main() -> None:
    client = AxionLabClient()

    # ── 1. 階層構造の準備 ──────────────────────────────────────
    print("=== Setup Hierarchy ===")
    org = client.orgs.create("ML Team")
    print(f"  Org: {org.name} ({org.org_id})")

    project = client.projects.create(org.org_id, "Summarization Eval")
    print(f"  Project: {project.name} ({project.project_id})")

    batch = client.batches.create(project.project_id, "2026-02 Model Comparison")
    print(f"  Batch: {batch.name} ({batch.batch_id})")

    # ── 2. 複数 Run + スコア Artifact 作成 ─────────────────────
    print("\n=== Create Runs with Score Artifacts ===")
    run_ids: list[str] = []

    for cfg in RUN_CONFIGS:
        run = client.runs.create(
            batch.batch_id,
            cfg["name"],
            tags=cfg["tags"],
            note=cfg["note"],
        )
        run_ids.append(run.run_id)
        print(f"\n  Run: {run.name} ({run.run_id})")

        # 各スコアを Artifact として登録
        scores: dict[str, int | float] = cfg["scores"]
        for metric_name, score_value in scores.items():
            # evaluation タイプはスコア系、latency/cost は専用タイプ
            if metric_name == "latency_p95_ms":
                art_type = "latency_p95_ms"
            elif metric_name == "cost_usd":
                art_type = "cost_usd"
            else:
                art_type = "evaluation"

            artifact = client.artifacts.create(
                run.run_id,
                kind="inline_number",
                type=art_type,
                label=metric_name,
                payload=score_value,
                meta={"metric": metric_name},
            )
            print(f"    artifact: {artifact.label} = {artifact.payload}")

        # 構造化されたスコアの全体像も JSON artifact として登録
        client.artifacts.create(
            run.run_id,
            kind="inline_json",
            type="evaluation",
            label="all-scores",
            payload=scores,
        )

    # ── 3. チャンピオン設定 ────────────────────────────────────
    # 最初の run をチャンピオン (ベースライン) として設定
    print("\n=== Set Champion ===")
    champion_run_id = run_ids[0]
    pin = client.pins.create(champion_run_id, "champion")
    print(f"  Champion pinned: run={champion_run_id}")
    print(f"  Pin: {pin}")

    # ── 4. DP ジョブ実行 ──────────────────────────────────────
    print("\n=== Trigger DP Computation ===")
    dp_job = client.dp.trigger(batch.batch_id, mode="active_only", recompute=False)
    print(f"  Job created: {dp_job.job_id} (status={dp_job.status})")

    # ジョブの完了を待機
    print("  Waiting for DP job to complete...", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        job_status = client.dp.get_job(dp_job.job_id)
        if job_status.status in ("succeeded", "failed", "canceled"):
            break
        print(".", end="", flush=True)
    print()

    print(f"  Job status: {job_status.status}")
    if job_status.status == "failed":
        print(f"  Error: {job_status.error_text or 'unknown'}")
        return

    # ── 5. Quality Metrics 確認 ────────────────────────────────
    print("\n=== Quality Metrics (per Run) ===")
    for run_id in run_ids:
        qm = client.quality_metrics.list_by_run(run_id)
        if not qm.items:
            print(f"  Run {run_id[:8]}...: (no metrics computed)")
            continue
        print(f"  Run {run_id[:8]}...:")
        for m in qm.items:
            print(f"    {m.key}: {m.value} (source={m.source})")

    # Batch 単位でキー別にまとめて取得
    print("\n=== Quality Metrics (Batch-level, key=mean_score) ===")
    batch_qm = client.quality_metrics.list_by_batch(batch.batch_id, key="mean_score")
    for m in batch_qm.items:
        print(f"  run={m.run_id[:8]}... mean_score={m.value}")

    # ── 6. Comparison Indicators 確認 ──────────────────────────
    print("\n=== Comparison Indicators (per Run) ===")
    for run_id in run_ids:
        ci = client.comparison_indicators.list_by_run(run_id)
        if not ci.items:
            print(f"  Run {run_id[:8]}...: (no indicators)")
            continue
        print(f"  Run {run_id[:8]}...:")
        for ind in ci.items:
            print(f"    {ind.key}: {ind.value} (vs {ind.baseline_ref})")

    # Batch 単位
    print("\n=== Comparison Indicators (Batch-level) ===")
    batch_ci = client.comparison_indicators.list_by_batch(batch.batch_id)
    for ind in batch_ci.items:
        print(
            f"  run={ind.run_id[:8]}... "
            f"{ind.key}={ind.value} "
            f"(vs {ind.baseline_ref})"
        )

    # ── Summary ──────────────────────────────────────────────
    print("\n=== Done ===")
    print(f"  Batch: {batch.name} ({batch.batch_id})")
    print(f"  Runs: {len(run_ids)}")
    print(f"  Champion: {run_ids[0][:8]}...")
    print("  DP job completed — Quality Metrics and Comparison Indicators computed.")


if __name__ == "__main__":
    main()
