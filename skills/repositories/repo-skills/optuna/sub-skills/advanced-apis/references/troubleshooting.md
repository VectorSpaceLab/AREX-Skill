# Advanced API Troubleshooting

Use this guide when an advanced Optuna support API behaves unexpectedly. Route core objective lifecycle issues to `../optimization-workflows/SKILL.md`, sampler/pruner algorithm issues to `../samplers-pruners/SKILL.md`, storage/CLI issues to `../cli-and-storage/SKILL.md`, and artifact/integration issues to `../artifacts-integrations/SKILL.md`.

## Install or Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'optuna'`
- `ModuleNotFoundError` for optional packages such as `torch`, `scipy`, plotting packages, or integration packages
- Importing `optuna.terminator` works, but a specific evaluator fails only when evaluated

Fixes:

- Verify the active Python environment with `python -c "import optuna; print(optuna.__version__)"`.
- For basic advanced APIs, the installed base dependencies are enough for logging, exceptions, search-space helpers, and simple terminator patterns.
- Avoid optional-heavy terminator evaluators such as `EMMREvaluator` when `torch` or `scipy` is absent; use a custom `BaseTerminator` or `BestValueStagnationEvaluator` plus `StaticErrorEvaluator` for portable workflows.
- Treat modules under `optuna._...` as private; if a private import breaks across versions, switch to a public study/sampler/visualization API or isolate the import behind a compatibility wrapper.

## Terminator Warnings and No-Ops

Symptoms:

- `FutureWarning` when constructing `Terminator`, `TerminatorCallback`, or calling `report_cross_validation_scores`
- Optimization does not stop when expected
- `ValueError: min_n_trials is expected to be a positive integer`
- `ValueError` about missing cross-validation scores

Causes and fixes:

- The terminator module is deprecated in Optuna 4.9.0 and planned for removal in 6.0.0. Keep warnings visible in migrations; filter them only in tests or intentional legacy workflows.
- `min_n_trials` must be at least `1`; use a small positive value in smoke tests.
- Termination requires `improvement < error`, not equality.
- `Terminator.should_terminate(study)` considers complete trials; failed/running/waiting trials do not count toward the complete-trial threshold.
- `CrossValidationErrorEvaluator` needs `report_cross_validation_scores(trial, scores)` inside the objective, and `scores` must contain at least two numbers.
- If the objective is deterministic and cross-validation error is not meaningful, use `BestValueStagnationEvaluator(max_stagnation_trials=...)` with `StaticErrorEvaluator(constant=0.0)` or a custom `BaseTerminator`.

## Search-Space Intersection Surprises

Symptoms:

- `IntersectionSearchSpace.calculate(study)` returns `{}` after successful trials
- A parameter disappears from the intersection
- `ValueError: IntersectionSearchSpace cannot handle multiple studies`

Causes and fixes:

- The intersection contains only parameters present with identical distributions in all considered finished trials.
- Conditional branches commonly remove branch-specific parameters from the intersection because not all trials suggest them.
- Reusing a parameter name with different ranges, log settings, steps, or distribution types removes that parameter from the intersection.
- Failed trials are ignored; pruned trials are ignored unless `include_pruned=True`.
- Create a new `IntersectionSearchSpace()` for each study, especially when using persistent storage where study IDs differ.
- Use `intersection_search_space(study.get_trials(deepcopy=False))` for a stateless calculation if caching is not needed.

## Hypervolume Errors

Symptoms:

- `ValueError` from `compute_hypervolume`
- Negative or unexpected values after using maximization objectives
- Slow calculations with many objectives

Causes and fixes:

- `compute_hypervolume` expects minimization-oriented loss vectors. For maximize objectives, multiply values by `-1` and choose the transformed reference point accordingly.
- Every point must dominate or equal the reference point coordinate-wise: `loss_vals <= reference_point`.
- Empty arrays return `0.0`; this is not an error.
- `assume_pareto=True` is only a speed hint for already Pareto-filtered inputs. Leave it `False` for safer diagnostics.
- Box decomposition may warn or slow down for more than four objectives; consider a different sampler or reduce objective count for diagnostics.

## Constraint Debugging

Symptoms:

- Warning that a trial does not have constraint values
- `ValueError: NaN is not acceptable as constraint value`
- `ValueError: Trials with different numbers of constraints cannot be compared`
- Feasible/infeasible ranking differs from expected Pareto dominance

Causes and fixes:

- A constraint function should return a tuple/list-like sequence of floats for every complete or pruned trial.
- A value `<= 0` means feasible; positive values are summed as violations for infeasible trials.
- Never return `NaN`; replace undefined constraints with a large positive violation or make the trial fail explicitly.
- Always return the same number of constraints for every trial in the same constrained study.
- If only some trials have constraint values, missing values can make trials dominated by constrained trials and produce warnings.

## Logging Problems

Symptoms:

- Duplicate Optuna logs in stderr and application log files
- `caplog` or root logger does not capture Optuna logs
- Too many Optuna `INFO` messages during tests

Fixes:

- To integrate with Python root logging, call `optuna.logging.enable_propagation()` and usually `optuna.logging.disable_default_handler()`.
- To restore Optuna stderr logging, call `optuna.logging.enable_default_handler()` and `optuna.logging.disable_propagation()`.
- To silence routine optimization logs, call `optuna.logging.set_verbosity(optuna.logging.WARNING)`.
- Use `optuna.logging.get_verbosity()` to confirm the effective Optuna library root level.

## Exceptions and Warning Filters

Symptoms:

- `ExperimentalWarning` appears during normal execution
- `TrialPruned` is treated as a failure by surrounding code
- `DuplicatedStudyError` or `UpdateFinishedTrialError` appears unexpectedly

Fixes:

- Filter `ExperimentalWarning` narrowly with `warnings.catch_warnings()` only around intentional experimental API calls.
- Raise `optuna.TrialPruned()` only after `trial.should_prune()` returns true; do not catch it inside the objective unless re-raising.
- Use `Study.optimize(..., catch=(ExpectedObjectiveError,))` for expected objective-level failures rather than catching Optuna configuration/storage errors globally.
- For duplicate study names, use `load_if_exists=True` with `create_study` only when resuming an existing study is intended.
- Do not call `Study.tell` twice for the same trial unless using `skip_if_finished=True` for idempotent external orchestration.

## Deterministic Smoke Check

Run the bundled script when verifying that advanced APIs import and behave in the active environment:

```bash
python scripts/terminator_smoke.py
```

Expected behavior:

- Imports `optuna`, `optuna.terminator`, `optuna.search_space`, and `optuna.logging`.
- Uses a custom deterministic terminator callback to stop a study before the requested `n_trials`.
- Verifies `IntersectionSearchSpace` returns the stable parameter while excluding conditional parameters.
- Checks a small internal hypervolume calculation only if the private helper is importable.
- Filters the known terminator `FutureWarning` so the smoke check stays deterministic.
