# Workflows

## 1. Summarize a finished run with a custom logger

Use this when you want the lifecycle table in a file, a notebook cell, or a structured log stream.

1. Create a `logging.Logger` and clear any stale handlers.
2. Pass it into `pygad.GA(..., logger=logger)`.
3. Run the GA.
4. Call `summary()` and keep the returned string if you want to archive the text.

```python
import logging
import pygad

logger = logging.getLogger("pygad.results")
logger.handlers.clear()
logger.setLevel(logging.INFO)
logger.propagate = False

file_handler = logging.FileHandler("run.log", mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(file_handler)

ga = pygad.GA(..., logger=logger)
ga.run()
summary_text = ga.summary()
```

### When to use it

- You need a human-readable summary of the optimizer configuration.
- You want the same messages in a log file and on screen.
- You are debugging callback wiring, selection choice, or save flags after a run completed.

## 2. Export plots in a headless script

Use this when you want PNG or PDF artifacts from a script, notebook, or CI job without opening a GUI.

1. Switch matplotlib to `Agg` before plotting.
2. Build a completed GA.
3. Call the plot methods you need with `save_dir=...`.
4. Close each returned figure after it is written.

```python
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

fig = ga.plot_fitness(save_dir="fitness.png")
plt.close(fig)
```

### Save-flag reminders

- `plot_new_solution_rate()`, `plot_fitness_band()`, `plot_population_diversity()`, `plot_non_dominated_hypervolume()`, and `plot_pareto_front_evolution()` need `save_solutions=True`.
- `plot_genes(solutions="best")` needs `save_best_solutions=True`.
- `plot_genes(solutions="all")` needs `save_solutions=True`.

### When to use it

- You need a figure for a report or issue ticket.
- You want to compare generations without opening a plot window.
- You are checking whether a completed run has converged, stalled, or collapsed into duplicates.

## 3. Export a PDF report

Use this when you want one file that bundles the configuration, summary, best solution, and applicable plots.

1. Install `pygad[report]`.
2. Run the GA to completion.
3. Call `generate_report()`.
4. Keep the returned path and inspect the PDF size or open it later.

```python
report_path = ga.generate_report(
    filename="my_run",
    title="My PyGAD run",
    include_plots="all",
    notes="Headless export for a finished optimization run.")
```

### Report controls

- `sections` changes both the content and the order of the PDF.
- `include_plots="all"` or `None` lets PyGAD pick the plots that match the run.
- `include_plots=[...]` restricts the report to specific plot method names.
- `page_size` accepts `"letter"` or `"A4"`.

### When to use it

- You want a reproducible handoff artifact for a completed GA run.
- You need the report to skip inapplicable plots automatically.
- You want a single export rather than many separate PNGs.

## 4. Debug a completed run from the artifacts

Use the plots as a diagnosis stack:

- `plot_new_solution_rate()`
  - low or flat values suggest repeated solutions or premature convergence.
- `plot_fitness_band()`
  - a narrowing band shows selection pressure and collapse in spread.
- `plot_population_diversity()`
  - a sharp drop means solutions are becoming similar.
- `plot_pareto_front_curve()`
  - good first check for 2- or 3-objective MOO runs.
- `plot_pareto_front_pcp()`
  - useful when the Pareto front has more than three dimensions.
- `plot_pareto_front_scatter_matrix()`
  - reveals objective pairs that are strongly correlated or conflicting.
- `plot_pareto_front_heatmap(sort_by=...)`
  - makes rank/order patterns obvious.
- `plot_non_dominated_hypervolume()`
  - a rising curve indicates the front is improving.
- `plot_pareto_front_evolution(every_k=...)`
  - shows whether the front is moving or already stable.

### Headless smoke pattern

For automated checks, combine the previous workflows with temporary files:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    tmpdir = Path(tmp)
    fig = ga.plot_fitness(save_dir=str(tmpdir / "fitness.png"))
    fig = ga.generate_report(filename=str(tmpdir / "report"))
```

The exact files can be deleted after the smoke run succeeds.
