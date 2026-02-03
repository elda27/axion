# Incremental Evaluation (DP)

Even though case-level values are second-class for UI,
they are required to compute run-level metrics.

Therefore all cases must be evaluated,
but we avoid full recomputation via DP.

Each case contributes a delta to run-level aggregates.

When a case changes:
- recompute its contribution
- update aggregate state

Garbage runs are excluded from DP.
