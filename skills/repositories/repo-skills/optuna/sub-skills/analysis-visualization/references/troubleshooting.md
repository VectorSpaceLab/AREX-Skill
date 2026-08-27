# Troubleshooting Analysis and Visualization

## Optional Dependency Missing

Symptoms:

- `ModuleNotFoundError: No module named 'plotly'`
- `ImportError` mentioning Plotly or Matplotlib version requirements.
- `ModuleNotFoundError: No module named 'pandas'` when calling `Study.trials_dataframe()`.
- `ModuleNotFoundError: No module named 'sklearn'` when using default fANOVA importances or `MeanDecreaseImpurityImportanceEvaluator`.

Fixes:

- Install Plotly for `optuna.visualization` plots: `python -m pip install 'plotly>=4.0.0'`.
- Install Matplotlib for `optuna.visualization.matplotlib`: `python -m pip install 'matplotlib>=3.0.0'`.
- Install pandas for `Study.trials_dataframe()`: `python -m pip install pandas`.
- Install scikit-learn for default fANOVA and MDI importances: `python -m pip install scikit-learn`.
- Use `PedAnovaImportanceEvaluator()` when a lightweight importance evaluator is acceptable and scikit-learn is not available.

Guard pattern:

```python
try:
    from optuna.visualization import plot_optimization_history
    fig = plot_optimization_history(study)
except (ImportError, ModuleNotFoundError) as exc:
    print(f"Skipping Plotly visualization: {exc}")
```

## Empty or Insufficient Study

Symptoms:

- Importance APIs raise `ValueError` for empty studies, studies with only pruned/failed trials, or too few completed trials for the evaluator.
- Visualization APIs emit warnings such as no completed trials and return empty figures.
- Intermediate-value plots have no useful content.

Fixes:

- Check completed trials before analysis:

```python
completed = [trial for trial in study.trials if trial.state.name == "COMPLETE"]
if len(completed) < 2:
    print("Run more completed trials before computing importances.")
```

- Use `plot_intermediate_values(study)` only when the objective called `trial.report(...)`.
- Use `plot_timeline(study)` to inspect failed, pruned, or running trial timing rather than objective progress.

## Multi-objective Target Misuse

Symptoms:

- `get_param_importances(study)` raises `ValueError` on a multi-objective study.
- Single-objective plot functions show confusing labels or values for multi-objective trials.

Fixes:

- Pass an explicit target for each objective or derived metric:

```python
from optuna.importance import PedAnovaImportanceEvaluator, get_param_importances

first_objective = get_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    params=["x", "y"],
    target=lambda trial: trial.values[0],
)
```

- Use `Study.set_metric_names([...])` before dataframe export or visualization when objective names matter.
- Use `plot_pareto_front` and `plot_hypervolume_history` for multi-objective overview plots.

## Conditional or Dynamic Search Spaces

Symptoms:

- Expected conditional parameters are missing from importance output.
- Importance computation raises `ValueError` when `params=[...]` names a parameter not present in enough completed trials.
- Dynamic parameter ranges can be rejected by importance evaluators.

Fixes:

- Remember that `params=None` evaluates only parameters present in all completed trials.
- Pass `params=[...]` for conditional parameters, but ensure completed trials exist with all requested parameters.
- Avoid interpreting importances across incompatible dynamic distributions; segment the study or analyze stable parameter subsets.

## Dataframe Export Issues

Symptoms:

- `Study.trials_dataframe()` fails because pandas is missing.
- Expected nested columns such as parameter names are flattened unexpectedly.
- Multi-objective values appear as `values` rather than `value`.

Fixes:

- Install pandas or skip dataframe export in minimal environments.
- Use `multi_index=True` for hierarchical columns.
- Use `attrs=("number", "value", "params", "state")` to limit dataframe size and columns.
- For multi-objective studies, expect `values` columns and consider `Study.set_metric_names([...])`.

## Plot Argument Errors

Symptoms:

- `plot_pareto_front` says it only supports 2 or 3 objectives or targets.
- `plot_hypervolume_history` says the study must be multi-objective.
- `plot_hypervolume_history` says reference point dimension is wrong.
- `target_names` length errors.

Fixes:

- For 4+ objectives, pass `targets=lambda trial: (trial.values[0], trial.values[1])` or another 2/3-dimensional projection to `plot_pareto_front`.
- Use `plot_optimization_history` instead of hypervolume for single-objective studies.
- Set `reference_point` length to exactly `len(study.directions)`.
- Set `target_names` length equal to the number of displayed objectives or targets.

## Backend Output Confusion

Symptoms:

- Code calls `write_html` on a Matplotlib `Axes`.
- Code calls `savefig` on a Plotly `Figure`.
- Plotly static image export fails despite Plotly being installed.

Fixes:

- Plotly returns `plotly.graph_objects.Figure`; use `fig.write_html("plot.html")` for portable output.
- Matplotlib returns `Axes` or arrays of axes; use `ax.figure.savefig("plot.png")` for a single axes object.
- Prefer Plotly HTML output when optional image-export packages are not guaranteed.
