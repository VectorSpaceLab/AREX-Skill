# Visualization Reference

Optuna exposes two visualization backends with nearly parallel APIs:

- Plotly backend: import functions from `optuna.visualization`; returns `plotly.graph_objects.Figure` objects.
- Matplotlib backend: import functions from `optuna.visualization.matplotlib`; returns `matplotlib.axes.Axes` or arrays of axes.

Use visualization after a study has trials. Study creation and optimization belong to the optimization workflow sub-skill.

## Backend Selection

Plotly example:

```python
from optuna.visualization import plot_optimization_history, plot_slice

fig = plot_optimization_history(study)
fig.write_html("optimization_history.html")

slice_fig = plot_slice(study, params=["lr", "depth"])
slice_fig.write_html("slice.html")
```

Matplotlib example:

```python
from optuna.visualization.matplotlib import plot_optimization_history, plot_slice

ax = plot_optimization_history(study)
ax.figure.savefig("optimization_history.png", bbox_inches="tight")

slice_axes = plot_slice(study, params=["lr", "depth"])
```

Optional dependency requirements:

- Plotly backend requires `plotly>=4.0.0`.
- Matplotlib backend requires `matplotlib>=3.0.0`.
- `plot_param_importances` can also require the selected importance evaluator dependencies, such as `scikit-learn` for default fANOVA.

## Single-objective Diagnostic Plot APIs

Plotly signatures:

```python
plot_optimization_history(study, *, target=None, target_name="Objective Value", error_bar=False)
plot_intermediate_values(study)
plot_parallel_coordinate(study, params=None, *, target=None, target_name="Objective Value")
plot_contour(study, params=None, *, target=None, target_name="Objective Value")
plot_slice(study, params=None, *, target=None, target_name="Objective Value")
plot_param_importances(study, evaluator=None, params=None, *, target=None, target_name="Objective Value")
plot_edf(study, *, target=None, target_name="Objective Value")
plot_rank(study, params=None, *, target=None, target_name="Objective Value")
plot_timeline(study, n_recent_trials=None)
plot_terminator_improvement(study, plot_error=False, improvement_evaluator=None, error_evaluator=None, min_n_trials=20)
```

The Matplotlib backend supports the same function names and signatures for these plots.

Common patterns:

```python
from optuna.importance import PedAnovaImportanceEvaluator
from optuna.visualization import plot_contour, plot_param_importances, plot_parallel_coordinate

plot_parallel_coordinate(study, params=["lr", "depth"])
plot_contour(study, params=["lr", "depth"])
plot_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    params=["lr", "depth"],
    target_name="Validation loss",
)
```

Use `target=...` when the plot should summarize a derived quantity rather than `trial.value`:

```python
plot_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    target=lambda trial: trial.duration.total_seconds(),
    target_name="Trial duration (seconds)",
)
```

`plot_intermediate_values(study)` is useful only when objective functions called `trial.report(value, step)` during optimization. Without intermediate values it can produce an empty or warning-only plot.

`plot_optimization_history` and `plot_edf` can accept a single `Study` or a sequence of studies for comparison.

## Multi-objective Visualization

Pareto front:

```python
from optuna.visualization import plot_pareto_front

fig = plot_pareto_front(
    study,
    target_names=["Latency", "Accuracy"],
    include_dominated_trials=True,
)
fig.write_html("pareto_front.html")
```

Signature:

```python
plot_pareto_front(
    study,
    *,
    target_names=None,
    include_dominated_trials=True,
    axis_order=None,
    constraints_func=None,
    targets=None,
)
```

Important Pareto-front rules:

- With `targets=None`, the study must have 2 or 3 objectives.
- For studies with more than 3 objectives, pass `targets=lambda trial: (...)` to project to 2 or 3 target values.
- If `targets` is used on an empty study, also pass `target_names` so axis labels can be inferred.
- `target_names` length must match the number of displayed targets.
- `axis_order` and `targets` cannot be used together.
- `constraints_func` follows Optuna constraint semantics: values `<= 0` are feasible and values `> 0` violate a constraint.

Hypervolume history:

```python
from optuna.visualization import plot_hypervolume_history

fig = plot_hypervolume_history(study, reference_point=[2.0, 2.0])
fig.write_html("hypervolume_history.html")
```

Signature:

```python
plot_hypervolume_history(study, reference_point)
```

Hypervolume rules:

- The study must be multi-objective.
- `len(reference_point)` must equal `len(study.directions)`.
- For single-objective studies, use `plot_optimization_history` instead.

## Exporting Figures Safely

Plotly:

```python
fig.write_html("plot.html")
```

Matplotlib:

```python
ax = plot_optimization_history(study)
ax.figure.savefig("plot.png", bbox_inches="tight")
```

Avoid assuming image export packages are installed. Plotly static image export can require extra packages, so `write_html` is the most portable Plotly output.

## Optional Dependency Guards

```python
try:
    from optuna.visualization import plot_optimization_history
except (ImportError, ModuleNotFoundError) as exc:
    raise RuntimeError("Install plotly to use optuna.visualization") from exc

try:
    fig = plot_optimization_history(study)
except ImportError as exc:
    raise RuntimeError("Plotly is required for this visualization") from exc
```

For backend-agnostic code, choose the backend at runtime:

```python
def plot_history(study, backend="plotly"):
    if backend == "matplotlib":
        from optuna.visualization.matplotlib import plot_optimization_history
    else:
        from optuna.visualization import plot_optimization_history
    return plot_optimization_history(study)
```
