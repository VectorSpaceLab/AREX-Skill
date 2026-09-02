---
name: reference_summary_checks
description: Load posteriordb reference posterior summaries and validate numeric quality fields for benchmark targets.
---

# Reference Summary Checks

Use this skill when a benchmark needs deterministic reference posterior summaries, especially posterior means and optional MCSE values, from a posteriordb-style snapshot. Do not use it to certify full MCMC quality when only summary files are available.

## Inputs

- `summary_path`: JSON file containing parameter names and numeric summary values.
- Optional `reference_info_path`: JSON metadata describing the reference posterior source and diagnostics.
- Optional `statistic`: summary vector key, defaulting to `mean_value`.

## Outputs

- A JSON report with `valid`, `statistic`, `values`, `mcse`, `quality_flags`, and `blockers`.
- Vector consistency and finite-number checks suitable for downstream scoring.

## Workflow

1. Parse the summary JSON and locate `names` plus the requested statistic vector.
2. Validate equal vector lengths and finite numeric values.
3. Attach MCSE values when `mcse_<statistic>` or `mcse_mean` is available with matching length.
4. Inspect reference-info metadata conservatively and record whether diagnostics are present.
5. Return blockers instead of inventing missing reference targets.

## Validation

Run `python scripts/reference_summary.py --summary <file> --output summary_report.json` or the included tests through `validate_skill_tree.py --run-tests`.

## Limitations

Summary schemas vary across databases. This skill focuses on deterministic summary loading and does not rerun reference samplers, compute R-hat, or download draw archives.
