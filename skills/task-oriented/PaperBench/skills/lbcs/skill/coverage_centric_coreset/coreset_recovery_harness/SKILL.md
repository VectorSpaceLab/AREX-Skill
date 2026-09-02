---
name: coreset_recovery_harness
description: Run a bounded CCS proxy experiment and emit validator-compatible recovery evidence.
---

# Coreset Recovery Harness

Use this skill during Paper2Skills recovery for Coverage-centric Coreset Selection when full CIFAR/ImageNet training is blocked by runtime cost or missing datasets. It builds a deterministic proxy dataset, invokes the generated scoring and selection skills, compares CCS against monotonic top-score selection, and runs a tiny optimizer update on the selected examples.

Do not use this harness to claim full paper accuracy. It produces soft-mode proxy evidence with explicit mechanism checks and source-boundary-safe logs.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing `training_dynamics_scoring` and `coverage_stratified_selection`.
- Output directory under the current attempt's `recovery/` tree.

## Outputs

- `recovery_result.json` with numeric `coverage_gain_over_monotonic`.
- `logs/generated_data_item.json` describing the synthetic benchmark.
- `logs/training_trace.json` with `params_before` and `params_after`.
- Mechanism checks that prove scoring, mislabel filtering, stratified coverage, and optimizer execution ran.

## Workflow

1. Construct a deterministic two-class score-stratified dataset.
2. Generate probability traces and call `training_dynamics_scoring.compute_scores`.
3. Call `coverage_stratified_selection.select_coverage_coreset` and `monotonic_selection`.
4. Measure coverage gain as represented score-bin fraction difference.
5. Run one logistic-regression-style gradient step on CCS-selected examples.
6. Save all validator-compatible artifacts from the executable command.

## Validation

Run `python tests/test_coreset_recovery_harness.py`; during recovery, run the script as `python scripts/run_proxy_recovery.py --attempt-dir ... --skills-root ...`.

## Limitations

This harness is intentionally small and deterministic. It verifies the mechanism, not the paper's full dataset accuracy.
