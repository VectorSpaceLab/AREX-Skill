---
name: results-and-visuals
description: "Summarize, plot, export, and debug completed PyGAD runs using
  summary, logger, plot_* methods, and PDF reports."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# results-and-visuals

Use this sub-skill when the task is to inspect, visualize, or export a completed `pygad.GA` run.

## Route elsewhere

- Tuning the optimizer, fitness, selection, crossover, mutation, callbacks, or save/load state: use `genetic-algorithm`.
- Built-in benchmarks and quality indicators: use `benchmarks`.
- GA-based neural-network adapters: use `neural-networks`.

## Operating flow

1. Confirm the run completed and that the data you need was saved:
   - `ga.generations_completed >= 1`
   - `save_solutions=True` for history-based plots
   - `save_best_solutions=True` for `plot_genes(solutions="best")`
2. Switch plotting to a headless backend before creating figures in scripts or CI.
3. Use `ga.summary()` to inspect the lifecycle table and the configured logger. Pass a custom `logging.Logger` through `pygad.GA(..., logger=...)` when you want file output or structured logs.
4. Call the needed `plot_*()` method and save it via `save_dir` when you want a file artifact.
5. Call `ga.generate_report()` when you want one PDF that bundles the run summary and applicable plots.

## Reference map

- API signatures, defaults, return values, and preconditions: [references/api-reference.md](references/api-reference.md)
- Reusable workflows for summaries, headless plots, and PDF exports: [references/workflows.md](references/workflows.md)
- Common failure modes and fixes: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled safe scripts

- [scripts/plot_report_smoke.py](scripts/plot_report_smoke.py): deterministic headless smoke that runs a small single-objective and multi-objective GA, prints a summary through a custom logger, writes temporary PNGs, and exports a temporary PDF report.

## Safety notes

- Plot methods need `matplotlib`; `generate_report()` needs both `matplotlib` and `reportlab`.
- `plot_new_solution_rate()`, `plot_fitness_band()`, `plot_population_diversity()`, `plot_non_dominated_hypervolume()`, and `plot_pareto_front_evolution()` require `save_solutions=True`.
- `plot_genes(solutions="best")` requires `save_best_solutions=True`; `plot_genes(solutions="all")` requires `save_solutions=True`.
- Pareto-front curve/evolution plots require a completed multi-objective run; the 2D/3D curve only supports 2 or 3 objectives.
