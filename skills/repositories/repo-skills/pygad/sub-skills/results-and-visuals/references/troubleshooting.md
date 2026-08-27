# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: ... can only be called after completing at least 1 generation` | `run()` has not finished yet, or the GA was never run. | Call `ga.run()` first and verify `ga.generations_completed >= 1`. |
| `ImportError: generate_report requires matplotlib` | `matplotlib` is not installed in the active environment. | Install `pygad[visualize]` or `pygad[report]`, then rerun in the same environment. |
| `ImportError: generate_report requires reportlab` | `reportlab` is missing. | Install `pygad[report]` or `reportlab`. |
| `plot_new_solution_rate() ... save_solutions=True` | The run did not record solution history. | Rebuild the GA with `save_solutions=True`. |
| `plot_genes() ... solutions='best' ... save_best_solutions=True` | Best-solution history was not recorded. | Rebuild the GA with `save_best_solutions=True`. |
| `plot_genes() ... solutions='all' ... save_solutions=True` | All-solution history was not recorded. | Rebuild the GA with `save_solutions=True`. |
| `plot_pareto_front_curve() ... 2 or 3 objectives` | The run is MOO but has too many objectives, or it is single-objective. | Use `plot_pareto_front_pcp()`, `plot_pareto_front_scatter_matrix()`, or `plot_pareto_front_heatmap()` for higher-dimensional fronts. |
| `... only works with multi-objective optimization problems` | A Pareto-only plot was called on a single-objective GA. | Switch to `plot_fitness()`, `plot_new_solution_rate()`, or another SOO-safe diagnostic. |
| `sort_by must be an integer in [0, ...]` | `plot_pareto_front_heatmap(sort_by=...)` used an out-of-range index. | Use `0 <= sort_by < num_objectives`, or pass `None` to keep the original order. |
| `objective_index must be in [0, ...]` | `plot_fitness_band(objective_index=...)` asked for a missing objective. | Pick a valid objective index for the run. |
| `every_k must be a positive integer` | `plot_pareto_front_evolution(every_k=...)` was given `0`, a negative number, or a non-integer. | Use an integer greater than zero. |
| `Unknown report sections` / `Unknown plot method(s)` / `Unknown page_size` | `generate_report()` was given an invalid name. | Use only `title`, `configuration`, `run_summary`, `best_solution`, `plots`, `notes`; plot method names from the API reference; and `letter` or `A4`. |
| A report is missing some plots | The run does not satisfy the preconditions for those plots. | This is expected. Enable the needed save flags or use a multi-objective run. |
| Duplicate logger lines | The same `logging.Logger` was reused with stale handlers. | Call `logger.handlers.clear()` before adding handlers, and set `propagate=False` for isolated output. |
| A `save_dir` or report file was not written | The parent directory was missing or the process had no write permission. | Create the directory first and write into a location the process can access. |

## Quick fixes

- For scripts and CI, set `MPLBACKEND=Agg` or call `matplotlib.use("Agg", force=True)` before plotting.
- When a plot or report seems to work but renders nothing useful, check whether the run saved the needed history or whether the objective count matches the plot family.
- For long-lived sessions, close figures after each plot to avoid piling up open matplotlib state.
