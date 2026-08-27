# API reference

## Logger and lifecycle summary

### `pygad.GA(..., logger=None)`

- The `logger` parameter accepts a standard `logging.Logger` instance.
- If `logger=None`, PyGAD creates a default console logger.
- The same logger is used by runtime messages and by `summary()`.

### `summary(line_length=70, fill_character=" ", line_character="-", line_character2="=", columns_equal_len=False, print_step_parameters=True, print_parameters_summary=True) -> str`

- Prints a Keras-style lifecycle table and returns the same text as one string.
- The rows cover the configured handlers for `on_start`, fitness, parent selection, crossover, mutation, generation, and stop.
- `print_step_parameters=True` keeps the per-step extras inside the table; `False` folds the extras into the global parameter block.
- Use a dedicated file or stream handler if you want the summary captured outside the console.
- In reused processes, clear stale handlers to avoid duplicate lines.

### Common logger pattern

```python
import logging

logger = logging.getLogger("pygad.run")
logger.handlers.clear()
logger.setLevel(logging.INFO)
logger.propagate = False
```

## Plot methods

All plot methods share the same base contract:

- they return a `matplotlib.figure.Figure`;
- they require `ga.generations_completed >= 1`;
- they save to `save_dir` when that argument is not `None`;
- they need `matplotlib` at call time, so a headless backend such as `Agg` is safest in scripts and CI.

### Plot inventory

| Method | Signature highlights | Preconditions / notes |
|---|---|---|
| `plot_fitness()` | `title="PyGAD - Generation vs. Fitness"`, `plot_type="plot"`, `color="#64f20c"`, `label=None` | Works for SOO and MOO. In MOO, pass per-objective iterables for `linewidth`, `color`, and `label` if you want custom styling. |
| `plot_new_solution_rate()` | `title="PyGAD - Generation vs. New Solution Rate"`, `plot_type="plot"`, `color="#64f20c"` | Requires `save_solutions=True`. Counts newly seen solutions per generation. |
| `plot_genes()` | `graph_type="plot"`, `solutions="all"`, `fill_color="#64f20c"`, `color="black"` | `solutions="all"` needs `save_solutions=True`; `solutions="best"` needs `save_best_solutions=True`. `graph_type` can be `plot`, `boxplot`, or `histogram`. |
| `plot_pareto_front_curve()` | `title="Pareto Front Curve"`, `label="Pareto Front"`, `color_fitness="#4169E1"`, `marker="o"` | MOO only. Supports only 2 or 3 objectives. |
| `plot_pareto_front_pcp()` | `title="Pareto Front - Parallel Coordinates"`, `color="#4169E1"`, `alpha=0.6` | MOO only. Works for any `M >= 2`. |
| `plot_pareto_front_scatter_matrix()` | `title="Pareto Front - Scatter Matrix"`, `marker="o"`, `alpha=0.6` | MOO only. Works for any `M >= 2`; especially useful when `M >= 4`. |
| `plot_pareto_front_heatmap()` | `title="Pareto Front - Heatmap"`, `cmap="viridis"`, `sort_by=0` | MOO only. Pass `sort_by=None` to keep the original order. |
| `plot_fitness_band()` | `title="PyGAD - Population fitness band"`, `objective_index=0`, `band_alpha=0.2` | Requires `save_solutions=True`. For MOO, choose the objective with `objective_index`. |
| `plot_non_dominated_hypervolume()` | `reference_point=None`, `title="PyGAD - Hypervolume per generation"` | Requires `save_solutions=True` and MOO. If `reference_point=None`, PyGAD uses column-wise min across all saved generations minus `0.1`. |
| `plot_population_diversity()` | `title="PyGAD - Population diversity"` | Requires `save_solutions=True`. Computes mean pairwise Euclidean distance per generation. |
| `plot_pareto_front_evolution()` | `every_k=1`, `title="Pareto Front Evolution"`, `cmap="viridis"` | Requires `save_solutions=True` and MOO. Supports only 2 or 3 objectives. `every_k` must be a positive integer. |

### Plot-family requirements at a glance

- `save_solutions=True`:
  - `plot_new_solution_rate()`
  - `plot_fitness_band()`
  - `plot_population_diversity()`
  - `plot_non_dominated_hypervolume()`
  - `plot_pareto_front_evolution()`
  - `plot_genes(solutions="all")`
- `save_best_solutions=True`:
  - `plot_genes(solutions="best")`
- MOO only:
  - `plot_pareto_front_curve()`
  - `plot_pareto_front_pcp()`
  - `plot_pareto_front_scatter_matrix()`
  - `plot_pareto_front_heatmap()`
  - `plot_non_dominated_hypervolume()`
  - `plot_pareto_front_evolution()`
- 2 or 3 objectives only:
  - `plot_pareto_front_curve()`
  - `plot_pareto_front_evolution()`

### Validation signals

- A successful plot call returns a figure object and, when `save_dir` is set, leaves a non-empty file on disk.
- If a plot is impossible for the current run, PyGAD raises `RuntimeError` or `ValueError` with a message that names the missing precondition.

## PDF report

### `generate_report(filename, title=None, sections=None, include_plots=None, figure_size_inches=(7.0, 4.5), notes=None, page_size="letter") -> str`

- Writes a PDF and returns the final file path.
- `.pdf` is appended automatically when `filename` has no suffix.
- The default section order is `title`, `configuration`, `run_summary`, `best_solution`, `plots`, `notes`.
- `sections` must be a subset of those names, and their order controls the PDF order.
- `include_plots=None` or `"all"` auto-selects every plot whose preconditions are satisfied by the current GA run.
- `include_plots` may also be a list of plot method names such as `plot_fitness` or `plot_pareto_front_curve`.
- `page_size` accepts `"letter"` or `"A4"`.
- The report uses `matplotlib` and `reportlab`, and it forces a headless matplotlib backend while building the PDF.

### Report-eligible plot names

The report can include the same plot methods listed above. It skips plots that are not applicable to the current run, such as Pareto plots on a single-objective GA or save-solution-based plots when the relevant history flags are disabled.

### Report validation signals

- A successful call returns a path ending in `.pdf` and writes a non-empty file.
- Unknown `sections`, `include_plots`, or `page_size` values raise `ValueError`.
- Calling it before any generation has completed raises `RuntimeError`.
- Missing `matplotlib` or `reportlab` raises `ImportError`.
