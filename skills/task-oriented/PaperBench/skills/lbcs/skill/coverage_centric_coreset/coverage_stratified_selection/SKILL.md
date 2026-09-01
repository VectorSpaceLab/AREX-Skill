---
name: coverage_stratified_selection
description: Select CCS-style coresets with mislabel filtering and deterministic score-stratified coverage.
---

# Coverage Stratified Selection

Use this skill after per-example importance scores are available and a high-pruning coreset must preserve distribution coverage. It implements the Coverage-centric Coreset Selection mechanism in a standard-library form: remove suspicious low-margin examples, bin the remaining examples by score, allocate budget across bins, and sample deterministically within each bin.

Do not use this skill as a generic top-k selector when coverage is irrelevant. Do not read or depend on the original paper repository during recovery.

## Inputs

- A score table with `indices`, `targets`, and a score key such as `accumulated_margin`.
- `coreset_ratio` in `(0, 1]` and optional `mis_ratio` in `[0, 1)`.
- `strata`, defaulting to 50 for paper-style behavior but often smaller in tests.
- A deterministic `seed` for repeatable within-bin selection.

## Outputs

- Selected original indices.
- Removed suspicious indices from the mislabel/easy-data mask.
- Strata budgets, represented bins, and class counts for mechanism checks.

## Workflow

1. Sort accumulated margin ascending and remove `mis_ratio` of the lowest-margin examples.
2. Compute a target coreset size from the original dataset size and `coreset_ratio`.
3. Bin remaining examples by the chosen score key.
4. Allocate budget across non-empty bins with the CCS low-occupancy-aware strategy.
5. Select deterministic representatives within each bin and emit diagnostics.

## Validation

Run `python tests/test_coverage_stratified_selection.py` or the Distiller skill-tree validator with tests enabled.

## Limitations

The standard-library implementation is designed for reproducible skill execution and recovery proxies. Full-scale image training can use the same contract around tensor-backed scores.
