# Optimization Workflow Troubleshooting

## Import or Installation Fails

Symptom: `ModuleNotFoundError: No module named 'optuna'`.

Fix:
- Install Optuna into the Python environment that runs the script: `python -m pip install optuna`.
- Verify with `python -c "import optuna; print(optuna.__version__)"`.
- Keep workflow examples limited to Optuna base features unless optional packages are installed. Plotting, pandas dataframes, scikit-learn examples, PyTorch examples, and integrations require extras not covered by this sub-skill.

## Optional Dependency Is Missing

Symptom: imports fail for `plotly`, `matplotlib`, `pandas`, `sklearn`, `torch`, `cmaes`, cloud clients, or dashboard/integration packages.

Fix:
- Replace the example with a pure-Python objective while validating Optuna workflow mechanics.
- Route visualization/importances to `analysis-visualization`.
- Route third-party framework integrations and artifacts to `artifacts-integrations`.
- Route sampler-specific dependencies such as CMA-ES behavior to `samplers-pruners`.

## Direction Argument Is Invalid

Symptoms:
- `ValueError` from `create_study(direction="test")`.
- `ValueError` from `create_study(direction=["maximize", "minimize"])`.
- `ValueError` from `create_study(directions="minimize")`.

Fix:
- Use `direction="minimize"` or `direction="maximize"` for one objective.
- Use `directions=["minimize", "maximize"]` for multiple objectives.
- Do not mix `direction` and `directions` in the same call.

## Objective Values Do Not Match Directions

Symptoms:
- A normal `Study.optimize` trial fails because the objective returns the wrong number of values.
- `Study.tell` with the wrong number of values warns and finalizes the trial as `TrialState.FAIL`.
- `Study.add_trial` raises when the imported trial's `value`/`values` length does not match the study directions.

Fix:
- Single objective: return one float from `objective` or call `study.tell(trial, value)`.
- Multi-objective: return a tuple/list with the same length as `directions`, or call `study.tell(trial, [value0, value1, ...])`.
- When importing trials with `study.add_trial`, use `value=...` for single-objective and `values=[...]` for multi-objective.
- If ask-and-tell already failed a trial due to a value-count mismatch, ask a new trial; do not try to retell the failed trial.

Minimal failing pattern to recognize:

```python
study = optuna.create_study(directions=["minimize", "maximize"])
trial = study.ask()
failed = study.tell(trial, 1.0)  # wrong: only one value for two directions
assert failed.state == optuna.trial.TrialState.FAIL
```

Correct pattern:

```python
trial = study.ask()
study.tell(trial, [1.0, 0.5])
```

## `best_trial` Fails or Is Not What You Need

Symptoms:
- `ValueError` when reading `study.best_trial` before any completed trial exists.
- Confusion in multi-objective studies where there is no single best trial.

Fix:
- Ensure at least one trial completed successfully before reading `best_trial`, `best_value`, or `best_params`.
- For multi-objective studies, use `study.best_trials` and inspect each Pareto trial's `values` and `params`.

## `report` or `should_prune` Fails

Symptoms:
- `NotImplementedError` in a multi-objective objective.
- `TypeError` from `trial.report(None, step)` or non-numeric values.
- `TypeError` from non-integer-like step values.
- `ValueError` from negative step values.
- Warning when reporting the same step twice.

Fix:
- Use `Trial.report` and `Trial.should_prune` only in single-objective studies.
- Pass a float-castable value and a non-negative integer step.
- Report each step once.
- In ask-and-tell, finish pruned trials with `study.tell(trial, state=optuna.trial.TrialState.PRUNED)`.

## Distribution Compatibility Error

Symptoms:
- `ValueError` after suggesting the same parameter name with incompatible methods or bounds.
- `ValueError` from `suggest_float(..., log=True, step=...)`.
- `ValueError` from `suggest_int(..., log=True, step=2)`.
- `ValueError` after changing categorical choices for the same parameter.

Fix:
- Use one stable distribution per parameter name throughout a study.
- Rename parameters when a conditional branch intentionally changes the search space shape.
- For log-scale floats, omit `step`.
- For log-scale integers, keep `step=1`.

Problem pattern:

```python
def objective(trial):
    trial.suggest_float("x", 0.0, 1.0)
    trial.suggest_int("x", 0, 10)  # incompatible reuse of name "x"
```

## Ask-and-Tell Trial Is Left Running or Finished Twice

Symptoms:
- Study contains unexpected running trials.
- `tell` raises when called again for an already finished trial.

Fix:
- Pair every `study.ask()` with exactly one `study.tell(...)` in normal control flow.
- Preserve `trial.number` when batching so each result maps to the correct trial.
- Use `skip_if_finished=True` only for idempotent retry cleanup; do not hide logic bugs in normal code.

## Callback or `study.stop()` Misuse

Symptoms:
- `RuntimeError` from `study.stop()` outside an active optimization.
- Callback does not stop when expected.

Fix:
- Call `study.stop()` only inside an objective or a callback invoked by `Study.optimize`.
- Callback signature must be `callback(study, frozen_trial) -> None`.
- The second callback argument is a `FrozenTrial`, not an active `Trial`; do not call active-only sampling logic on it except replaying already stored `suggest_*` parameters.

## Duplicate, Missing, Copy, or Delete Study Errors

Symptoms:
- Duplicate-study error when creating or copying to an existing `study_name`.
- `KeyError` when loading or deleting a missing study.
- `ValueError` when `load_study(study_name=None, storage=...)` is ambiguous because multiple studies exist.

Fix:
- For resume behavior, create with `load_if_exists=True`.
- For explicit load/delete, pass the exact `study_name`.
- For copy, choose `to_study_name` when the destination storage already has the source name.
- Route persistent storage design and CLI operations to `cli-and-storage`.

## Objective Exceptions Stop Optimization

Symptom: optimization stops after a trial fails and the exception is re-raised.

Fix:
- If failures are expected and should be recorded as failed trials, pass `catch=(ExpectedError,)` to `Study.optimize`.
- Do not catch `optuna.TrialPruned` as a failure; raise it to record a pruned trial in normal pruning workflows.
- Inspect `trial.state` in callbacks or `study.trials` to distinguish `COMPLETE`, `PRUNED`, and `FAIL`.
