#!/usr/bin/env python3
"""Axion クイックスタート: 基本フローの一通りの実行.

Org → Project → Batch → Run → Artifact を作成し、
一覧取得・単体取得を確認する最小限のサンプルです。

Usage:
    uv run python examples/quickstart.py
"""

from __future__ import annotations

from axion import AxionClient


def main() -> None:
    client = AxionClient()

    # ── 0. ヘルスチェック ──────────────────────────────────────
    print("=== Health Check ===")
    h = client.health_check()
    print(f"  status: {h}")

    # ── 1. Organization 作成 ──────────────────────────────────
    print("\n=== Create Organization ===")
    org = client.orgs.create("Example Org")
    print(f"  created: {org.name} (id={org.org_id})")

    # 取得確認
    org_get = client.orgs.get(org.org_id)
    print(f"  fetched: {org_get.name}")

    # 一覧取得
    orgs = client.orgs.list()
    print(f"  total orgs: {len(orgs.items)}")

    # ── 2. Project 作成 ──────────────────────────────────────
    print("\n=== Create Project ===")
    project = client.projects.create(org.org_id, "Summarization Eval")
    print(f"  created: {project.name} (id={project.project_id})")

    projects = client.projects.list(org.org_id)
    print(f"  projects in org: {len(projects.items)}")

    # ── 3. Batch 作成 ─────────────────────────────────────────
    print("\n=== Create Batch ===")
    batch = client.batches.create(project.project_id, "2026-02 Prompt Iteration")
    print(f"  created: {batch.name} (id={batch.batch_id})")

    batches = client.batches.list(project.project_id)
    print(f"  batches in project: {len(batches.items)}")

    # ── 4. Run 作成 ───────────────────────────────────────────
    print("\n=== Create Run ===")
    run = client.runs.create(
        batch.batch_id,
        "run-v1-gpt4o",
        tags=["gpt-4o", "prompt-v1"],
        note="GPT-4o with initial prompt template",
    )
    print(f"  created: {run.name} (id={run.run_id})")
    print(f"  status: {run.status}, tags: {run.tags}")

    # 取得確認
    run_get = client.runs.get(run.run_id)
    print(f"  fetched: {run_get.name}")

    runs = client.runs.list(batch.batch_id)
    print(f"  runs in batch: {len(runs.items)}")

    # ── 5. Artifact 作成 ──────────────────────────────────────
    print("\n=== Create Artifacts ===")

    # 5-a. URL artifact (Langfuse trace link)
    a_url = client.artifacts.create(
        run.run_id,
        kind="url",
        type="langfuse_trace",
        label="Langfuse Trace",
        payload="https://langfuse.example.com/trace/abc123",
        meta={"traceId": "abc123"},
    )
    print(f"  [url]          {a_url.label} → {a_url.payload}")

    # 5-b. Inline text artifact (note / memo)
    a_text = client.artifacts.create(
        run.run_id,
        kind="inline_text",
        type="note",
        label="Experiment Note",
        payload="GPT-4o generated concise summaries but missed key entities.",
    )
    print(f"  [inline_text]  {a_text.label}")

    # 5-c. Inline number artifact (score)
    a_score = client.artifacts.create(
        run.run_id,
        kind="inline_number",
        type="evaluation",
        label="ROUGE-L Score",
        payload=0.847,
        meta={"metric": "rouge-l", "variant": "f-measure"},
    )
    print(f"  [inline_number] {a_score.label} = {a_score.payload}")

    # 5-d. Inline JSON artifact (structured evaluation result)
    a_json = client.artifacts.create(
        run.run_id,
        kind="inline_json",
        type="evaluation",
        label="Detailed Scores",
        payload={
            "rouge-1": 0.912,
            "rouge-2": 0.783,
            "rouge-l": 0.847,
            "bleu": 0.654,
            "bertscore": 0.891,
        },
    )
    print(f"  [inline_json]  {a_json.label} → {a_json.payload}")

    # 5-e. Inline number artifact (latency)
    a_latency = client.artifacts.create(
        run.run_id,
        kind="inline_number",
        type="latency_p95_ms",
        label="P95 Latency",
        payload=1250,
    )
    print(f"  [inline_number] {a_latency.label} = {a_latency.payload} ms")

    # 5-f. Inline number artifact (cost)
    a_cost = client.artifacts.create(
        run.run_id,
        kind="inline_number",
        type="cost_usd",
        label="Total Cost",
        payload=4.32,
    )
    print(f"  [inline_number] {a_cost.label} = ${a_cost.payload}")

    # 一覧取得
    artifacts = client.artifacts.list(run.run_id)
    print(f"\n  total artifacts for run: {len(artifacts.items)}")
    for a in artifacts.items:
        print(f"    - [{a.kind}] {a.label}")

    # ── Summary ──────────────────────────────────────────────
    print("\n=== Done ===")
    print(f"  Org:      {org.name} ({org.org_id})")
    print(f"  Project:  {project.name} ({project.project_id})")
    print(f"  Batch:    {batch.name} ({batch.batch_id})")
    print(f"  Run:      {run.name} ({run.run_id})")
    print(f"  Artifacts: {len(artifacts.items)} created")


if __name__ == "__main__":
    main()
