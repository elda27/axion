#!/usr/bin/env python3
"""Axion Lab チャンピオン比較: ベースライン vs 候補 Run の比較ワークフロー.

チャンピオン Run を設定し、新しい候補 Run と比較するユースケースを示します。
Pin の操作、RunSummary の取得、Run のステータス変更 (garbage 運用) を含みます。

Usage:
    uv run python examples/champion_comparison.py
"""

from __future__ import annotations

from axion_lab import AxionLabClient


def main() -> None:
    client = AxionLabClient()

    # ── 1. セットアップ ──────────────────────────────────────
    print("=== Setup ===")
    org = client.orgs.create("Research Lab")
    project = client.projects.create(org.org_id, "Image Segmentation")
    batch = client.batches.create(project.project_id, "SAM vs SegGPT Comparison")
    print(f"  Batch: {batch.name} ({batch.batch_id})")

    # ── 2. ベースライン Run (チャンピオン候補) ────────────────
    print("\n=== Create Baseline Run ===")
    baseline = client.runs.create(
        batch.batch_id,
        "baseline-sam-vit-h",
        tags=["sam", "vit-h", "baseline"],
        note="SAM ViT-H baseline model on COCO val2017 subset",
    )
    print(f"  Run: {baseline.name} ({baseline.run_id})")

    # ベースラインスコア
    for label, value in [
        ("mIoU", 0.782),
        ("mAP@50", 0.891),
        ("mAP@75", 0.734),
        ("fps", 12.3),
    ]:
        client.artifacts.create(
            baseline.run_id,
            kind="inline_number",
            type="evaluation",
            label=label,
            payload=value,
        )
    print("  Scores: mIoU=0.782, mAP@50=0.891, mAP@75=0.734, fps=12.3")

    # チャンピオンに設定
    client.pins.create(baseline.run_id, "champion")
    print("  → Pinned as champion")

    # ── 3. 候補 Run の作成 ────────────────────────────────────
    print("\n=== Create Candidate Runs ===")
    candidates = [
        {
            "name": "candidate-seggpt",
            "tags": ["seggpt", "candidate"],
            "note": "SegGPT with in-context learning",
            "scores": {"mIoU": 0.798, "mAP@50": 0.903, "mAP@75": 0.756, "fps": 8.7},
        },
        {
            "name": "candidate-sam2",
            "tags": ["sam2", "candidate"],
            "note": "SAM 2 with Hiera backbone",
            "scores": {"mIoU": 0.821, "mAP@50": 0.925, "mAP@75": 0.789, "fps": 15.1},
        },
        {
            "name": "candidate-sam-vit-b",
            "tags": ["sam", "vit-b", "candidate"],
            "note": "SAM ViT-B (smaller, faster)",
            "scores": {"mIoU": 0.712, "mAP@50": 0.834, "mAP@75": 0.681, "fps": 28.5},
        },
    ]

    candidate_ids: list[str] = []
    for cfg in candidates:
        run = client.runs.create(
            batch.batch_id,
            cfg["name"],
            tags=cfg["tags"],
            note=cfg["note"],
        )
        candidate_ids.append(run.run_id)
        print(f"\n  Run: {run.name} ({run.run_id})")

        for label, value in cfg["scores"].items():
            client.artifacts.create(
                run.run_id,
                kind="inline_number",
                type="evaluation",
                label=label,
                payload=value,
            )
        scores_str = ", ".join(f"{k}={v}" for k, v in cfg["scores"].items())
        print(f"  Scores: {scores_str}")

    # ── 4. User Selected ピン ─────────────────────────────────
    # 注目したい run を user_selected としてピン留め
    print("\n=== Pin User Selected ===")
    best_candidate_id = candidate_ids[1]  # sam2
    client.pins.create(best_candidate_id, "user_selected")
    print(f"  Pinned {candidates[1]['name']} as user_selected")

    # ── 5. Run Summary の取得 ─────────────────────────────────
    print("\n=== Run Summary ===")
    summary = client.runs.summary(batch.batch_id)

    if summary.champion:
        print(
            f"  Champion: {summary.champion.name} "
            f"({summary.champion.run_id[:8]}...)"
        )

    recent = summary.recent_collapsed.runs
    print(f"  Recent: {len(recent)} runs")
    for r in recent:
        print(f"    - {r.name}")

    print(f"  User Selected: {len(summary.user_selected)} runs")
    for r in summary.user_selected:
        print(f"    - {r.name}")

    print(f"  Others: {len(summary.others.runs)} runs")
    for r in summary.others.runs:
        print(f"    - {r.name}")

    # ── 6. Garbage 運用 ───────────────────────────────────────
    # 成績の悪い run を garbage にする (非表示化、復活可能)
    print("\n=== Garbage Management ===")
    worst_id = candidate_ids[2]  # sam-vit-b
    print(f"  Moving {candidates[2]['name']} to garbage...")
    updated = client.runs.update(worst_id, status="garbage")
    print(f"  Status: {updated.status}")

    # garbage を除外した一覧
    active_runs = client.runs.list(batch.batch_id, include_garbage=False)
    print(f"  Active runs: {len(active_runs.items)}")
    for r in active_runs.items:
        print(f"    - {r.name} [{r.status}]")

    # garbage を含めた一覧
    all_runs = client.runs.list(batch.batch_id, include_garbage=True)
    print(f"  All runs (with garbage): {len(all_runs.items)}")

    # garbage から復活
    print(f"\n  Restoring {candidates[2]['name']} from garbage...")
    restored = client.runs.update(worst_id, status="active")
    print(f"  Status: {restored.status}")

    # ── 7. チャンピオン交代 ────────────────────────────────────
    print("\n=== Champion Upgrade ===")
    # SAM 2 が最高成績なのでチャンピオンを変更
    new_champion_id = candidate_ids[1]  # sam2
    print(f"  Upgrading champion to {candidates[1]['name']}...")

    # 新しい run に champion ピンを設定
    # (自動的に旧チャンピオンの champion ピンは解除される)
    client.pins.create(new_champion_id, "champion")
    print(f"  New champion: {candidates[1]['name']}")

    # 確認
    summary_after = client.runs.summary(batch.batch_id)
    if summary_after.champion:
        print(f"  Verified champion: {summary_after.champion.name}")

    # user_selected ピンを解除
    print("\n=== Unpin User Selected ===")
    client.pins.delete(new_champion_id, "user_selected")
    print(f"  Unpinned user_selected from {candidates[1]['name']}")

    # ── Summary ──────────────────────────────────────────────
    print("\n=== Done ===")
    print(f"  Batch: {batch.name}")
    print(f"  Total runs: {len(candidate_ids) + 1}")
    print(f"  Champion: {candidates[1]['name']} (upgraded from baseline)")
    print("  Demonstrated: pins, summary, garbage/restore, champion upgrade")


if __name__ == "__main__":
    main()
