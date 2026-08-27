---
name: analysis-visualization
description: "Analyze completed Optuna studies with parameter importances, trial
  dataframes, diagnostic plots, Plotly/Matplotlib backends, Pareto fronts,
  hypervolume history, and optional dependency checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optuna Analysis and Visualization

Use this sub-skill after trials already exist and the task is to inspect, export, rank, or visualize study results. It covers `optuna.importance`, `Study.trials_dataframe`, `optuna.visualization`, and `optuna.visualization.matplotlib`.

## Route Here For

- Computing parameter importances with `optuna.importance.get_param_importances`.
- Exporting trial records with `Study.trials_dataframe` for tabular analysis or CSV output.
- Creating optimization-history, intermediate-value, contour, slice, parallel-coordinate, EDF, rank, timeline, and importance plots.
- Visualizing multi-objective Pareto fronts and hypervolume history.
- Handling missing optional packages such as `plotly`, `matplotlib`, `pandas`, or `scikit-learn` gracefully.

## Route Elsewhere

- Use `../optimization-workflows/SKILL.md` for creating studies, defining objectives, running trials, `ask`/`tell`, callbacks, pruning reports, and trial generation.
- Use `../samplers-pruners/SKILL.md` for choosing or configuring samplers, pruners, constraints, seeds, and pruning algorithms.
- Use `../cli-and-storage/SKILL.md` for CLI usage, storage URLs, RDB-backed study loading, study creation from a shell, and persistent storage operations.

## Start With These References

- Analysis APIs and data export: `references/analysis-reference.md`
- Plotting APIs and backend selection: `references/visualization-reference.md`
- Common failures and optional dependencies: `references/troubleshooting.md`

## Safe Smoke Checks

Run these scripts from this sub-skill directory in any environment with `optuna` installed. They create small deterministic in-memory studies and do not use network, external datasets, or persistent storage.

```bash
python scripts/analysis_smoke.py
python scripts/visualization_smoke.py
```

Expected behavior in a minimal install:

- `analysis_smoke.py` reports a successful core importance check with `PedAnovaImportanceEvaluator`, and skips dataframe or default fANOVA checks if `pandas` or `scikit-learn` are missing.
- `visualization_smoke.py` reports Plotly and Matplotlib checks as skipped when those optional backends are not installed.

## Minimal Patterns

```python
import optuna
from optuna.importance import PedAnovaImportanceEvaluator, get_param_importances

study = optuna.create_study(direction="minimize")
study.optimize(lambda trial: (trial.suggest_float("x", -2.0, 2.0) - 0.5) ** 2, n_trials=8)

importances = get_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    params=["x"],
)
```

```python
from optuna.visualization import plot_optimization_history, plot_slice

fig = plot_optimization_history(study)
fig.write_html("optimization_history.html")

slice_fig = plot_slice(study, params=["x"])
slice_fig.write_html("slice.html")
```
