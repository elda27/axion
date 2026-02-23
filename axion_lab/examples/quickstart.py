#!/usr/bin/env python3
"""Axion Lab クイックスタート: high-level API で最小登録.

前提:
    AXION_LAB_ORG / AXION_LAB_PROJECT / AXION_LAB_BATCH を `.env` に設定

Usage:
    uv run python examples/quickstart.py
"""

import os

from axion_lab.high_level import create_artifact, create_run

os.environ["AXION_LAB_ORG"] = "exp"
os.environ["AXION_LAB_PROJECT"] = "test"
os.environ["AXION_LAB_BATCH"] = "example"


def main() -> None:
    print("=== Create Run (high-level) ===")
    run = create_run(
        "run-v1-gpt4o",
        tags=["gpt-4o", "prompt-v1"],
        note="GPT-4o with initial prompt template",
    )
    print(f"  created: {run.name} (id={run.run_id})")

    print("\n=== Create Artifacts (high-level) ===")
    score = create_artifact(
        kind="inline_number",
        type="evaluation",
        label="ROUGE-L Score",
        payload=0.847,
        meta={"metric": "rouge-l", "variant": "f-measure"},
    )
    print(f"  [inline_number] {score.label} = {score.payload}")

    trace = create_artifact(
        kind="url",
        type="langfuse_trace",
        label="Langfuse Trace",
        payload="https://langfuse.example.com/trace/abc123",
    )
    print(f"  [url] {trace.label} -> {trace.payload}")

    print("\n=== Done ===")
    print(f"  Run: {run.name} ({run.run_id})")


if __name__ == "__main__":
    main()
    main()
    main()
