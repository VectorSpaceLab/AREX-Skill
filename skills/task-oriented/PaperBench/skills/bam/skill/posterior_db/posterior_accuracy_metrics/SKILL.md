---
name: posterior_accuracy_metrics
description: Compute posterior moment accuracy metrics for approximate draws against reference posterior summaries.
---

# Posterior Accuracy Metrics

Use this skill when approximate posterior draws or estimates must be scored against posteriordb reference summaries. It is appropriate for reduced recovery experiments because it preserves the paper's moment-accuracy mechanism without requiring full Stan sampling.

## Inputs

- Approximate draws as a list of records, a dictionary of parameter arrays, or precomputed parameter means.
- Reference mean values keyed by parameter name.
- Optional squared-moment references keyed by parameter name.

## Outputs

- `mean_rmse`, `per_parameter` errors, parameter overlap, missing approximate parameters, and optional `squared_moment_rmse`.
- JSON suitable for recovery-result metrics and ablation checks.

## Workflow

1. Normalize approximate inputs into parameter arrays or means.
2. Intersect approximate and reference parameter names.
3. Compute signed mean errors and RMSE over the overlap.
4. Compute squared-moment RMSE separately when squared references are supplied.
5. Return missing-name accounting instead of silently treating absent parameters as zero.

## Validation

Run `python scripts/accuracy_metrics.py --approx approx.json --reference ref.json --output metrics.json` or the included tests via `validate_skill_tree.py --run-tests`.

## Limitations

This skill does not decide whether a reference summary is trustworthy. Pair it with the reference-summary skill for quality checks and with a benchmark harness for provenance and cost reporting.
