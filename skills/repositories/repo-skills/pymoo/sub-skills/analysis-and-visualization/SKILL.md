---
name: analysis-and-visualization
description: "Postprocess pymoo results with indicators, Pareto analysis,
  reference directions, decomposition, MCDM, convergence traces, and headless
  plots."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# analysis-and-visualization

Use this sub-skill when a pymoo task asks to interpret or postprocess completed
optimization results: hypervolume, IGD/GD, epsilon indicators, KKTPM, R-metric,
Pareto-front or Pareto-set analysis, reference directions, decomposition
functions, MCDM/knee-point selection, convergence from `res.history`, or saving
visualizations in a headless environment.

## Route first

- Running `minimize`, choosing algorithms, termination, callbacks, checkpoints,
  or ask-and-tell optimization loops belongs to `optimization-workflows`.
- Defining problems, bounds, objective/constraint shapes, `G <= 0`, or Pareto
  front/set methods belongs to `problem-modeling`.
- Parallel evaluation, optional distributed backends, compiled-extension speed,
  and long-run resource tuning belongs to `performance-and-parallelization`.
- Stay here for objective-space quality metrics, post-run selection, reference
  direction matrices, scalarization of objective matrices, convergence plots,
  and static/animated visual summaries.

## Fast operating checklist

1. **Normalize the data contract**: treat objective values as a finite 2-D
   minimization matrix `F` with shape `(n_points, n_obj)`. Pareto fronts `pf`
   need the same number of columns. Hypervolume reference points must be worse
   than the relevant front in every objective.
2. **Choose metrics by available evidence**: use `GD`, `GDPlus`, `IGD`,
   `IGDPlus`, and epsilon only when a true or accepted approximate Pareto front
   is available. If no front is available, prefer hypervolume with an explicit
   reference point, history-based convergence, or KKTPM when differentiable
   problem gradients are available.
3. **Separate final-set quality from convergence**: final `res.F` or
   `res.opt.get("F")` scores one set; `save_history=True` stores snapshots in
   `res.history` for curves but can be memory intensive.
4. **Use decomposition and MCDM for selection**: normalize objective scales,
   then rank rows with ASF/AASF, weighted sum, Tchebicheff, PBI, pseudo weights,
   or high-tradeoff point detection. Keep selected indices tied back to the
   original `res.X` and `res.F` rows.
5. **Generate reference directions deliberately**: `uniform`/`das-dennis` use
   partition counts and only create achievable point counts; `energy` and
   `reduction` can target arbitrary counts; `multi-layer`, `layer-energy`, and
   `incremental` cover specialized layouts.
6. **Make plots headless-safe**: set a non-interactive Matplotlib backend such
   as `Agg` before importing pymoo visualization helpers, then call `.save(...)`
   instead of relying on `.show()`.

## Open the bundled references

- [Analysis API reference](references/analysis-api-reference.md): imports,
  minimal signatures, input requirements, output meaning, and version caveats
  for indicators, non-dominated sorting, reference directions, decomposition,
  MCDM, and visualization helpers.
- [Postprocessing workflows](references/postprocessing-workflows.md): recipes for
  final indicator calculation, Pareto-front-unknown analysis, MCDM solution
  selection, convergence/history curves, and headless static/optional video
  plotting.
- [Troubleshooting](references/troubleshooting.md): fixes for reference-point,
  ideal/nadir, missing Pareto front, invalid shape, normalization, headless
  display, optional animation, KKTPM, R-metric, and decomposition mistakes.

## Bundled scripts

- [scripts/check_indicators.py](scripts/check_indicators.py): deterministic
  numeric checks for core indicators plus small sanity checks for reference
  directions, decomposition, and MCDM selection.
- [scripts/save_scatter_plot.py](scripts/save_scatter_plot.py): headless `Agg`
  scatter-plot save workflow with assertions that the image file was created.
