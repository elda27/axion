# Core Concepts

## Run
One execution of a pipeline over many samples (cases).
A run represents a distribution, not a single output.

## Case
One sample (one row, one image, one conversation, one document).
Case-level is second-class for UI, but required for computation.

## OutputRow
All outputs (intermediate and final) are stored as flat rows.
No system-level distinction between intermediate and final.

Meaning (stage, agent, etc.) is expressed by user-defined columns.

## Artifact
The actual generated content referenced by OutputRow.

## Quality Metric
A run-level metric that evaluates the quality of a run.

## Comparison Indicator
A metric derived from comparing runs.

## Health / Coverage Indicator
Metrics describing representativeness and stability of a run.
