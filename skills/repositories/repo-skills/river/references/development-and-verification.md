# Development and Verification Guidance

## When to read

Read this for River checkout maintenance: adding or changing estimators, selecting focused tests, diagnosing build issues, or verifying that generated skill guidance still matches the source. If you are only using River as an installed package, start with the workflow sub-skills instead.

## Maintainer constraints to preserve

- Estimator `__init__` parameters should be explicit and type-hinted.
- New estimators should either have usable defaults or implement `_unit_test_params()` so automated checks can instantiate them.
- Estimators that cannot pass a specific generic check should expose `_unit_test_skips()` with a narrow reason.
- The key online API is incremental: `learn_one`, `predict_one`, `predict_proba_one`, `transform_one`, and mini-batch `*_many` methods where implemented.
- Tests should be at least as thorough as the implementation. A representative `checks.check_estimator(...)` pass is the minimum for a new estimator.
- Speed matters for River; do not turn a per-sample hot path into repeated signature inspection, dataframe conversion, or large allocation without a reason.

## Focused verification commands

Use the repository's own current tooling when working in a checkout. Common commands are:

```sh
uv sync
uv run pytest
uv run pytest tests/linear_model/test_glm.py
uv run prek run --all-files
uv run mypy
```

For package-use verification outside a checkout, use the bundled smoke scripts instead:

```sh
python scripts/check_river_environment.py
python sub-skills/online-core-api/scripts/estimator_contract_smoke.py
python sub-skills/pipelines-and-features/scripts/pipeline_feature_smoke.py
python sub-skills/streaming-evaluation/scripts/stream_evaluation_smoke.py
python sub-skills/supervised-models/scripts/supervised_model_smoke.py
python sub-skills/specialized-workflows/scripts/specialized_workflows_smoke.py
```

## Estimator-check workflow

1. Instantiate the estimator with the smallest meaningful defaults.
2. Run a tiny learn/predict/transform smoke loop so obvious target or feature-type problems surface quickly.
3. Run `checks.check_estimator(estimator)` or the specific check produced by `checks.yield_checks(estimator)`.
4. If a check fails, inspect whether the estimator violates a general River contract or legitimately needs a narrow `_unit_test_skips()` entry.
5. Add model-family tests for edge cases not covered by generic checks, such as sample weights, multiclass targets, empty predictions, or optional dependency behavior.

## Build and dependency notes

- Source installs build a Rust extension through maturin. Released wheels are simpler for package use.
- The optional `pandas` extra is selected only for mini-batch/DataFrame workflows.
- `scikit-learn` is needed for sklearn compatibility wrappers and selected compatibility tests, not for River's core online interface.
- Docs, benchmark, CodSpeed, and notebook dependencies are not part of the minimal runtime unless the task explicitly targets those workflows.

## Evidence boundaries

The generated runtime skill is self-contained. Do not tell future agents to run original notebooks or tests as part of using the skill. Use the bundled scripts for operational smoke checks, and use the source repository's native tests only when doing checkout maintenance.
