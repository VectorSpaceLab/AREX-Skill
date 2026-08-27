---
name: performance-and-parallelization
description: "Speed up and harden pymoo runs with vectorized problems,
  elementwise parallel runners, optional backends, compiled-extension checks,
  and long-run resource controls."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# performance-and-parallelization

Use this sub-skill when a pymoo task asks to make optimization faster or safer:
slow objective evaluations, vectorization, elementwise runners, `starmap`,
threads/processes, joblib/dask/ray, GPU acceleration patterns, compiled-extension
status, reproducibility, progress overhead, or memory costs during long runs.

## Route first

- Problem formulas, objective/constraint signs, output shapes, and bounds belong
  to the `problem-modeling` sub-skill.
- Algorithm portfolio, termination choices, ask-and-tell loops, and result field
  interpretation belong to the `optimization-workflows` sub-skill.
- Indicators, Pareto-front metrics, convergence plots, and visualization belong
  to the `analysis-and-visualization` sub-skill.
- Stay here for evaluation throughput, backend selection, install extras for
  parallelization, compiled-function checks, and resource cleanup.

## Fast operating checklist

1. **Prefer vectorized evaluation**: if an objective can evaluate an `(n, n_var)`
   NumPy matrix at once, use `Problem` and fill vectorized arrays such as
   `out["F"]`. This usually beats Python-level pools for cheap numeric work.
2. **Use elementwise runners for expensive black boxes**: if one simulation call
   evaluates one candidate at a time, define `ElementwiseProblem` and pass an
   `elementwise_runner` such as `StarmapParallelization(pool.starmap)`.
3. **Choose the smallest backend that fits**: stdlib threads/processes need only
   the base pymoo install; joblib/dask/ray require the `parallelization` optional
   extra and should not be assumed present.
4. **Always clean up pools/clients**: close/join thread or process pools, close
   dask clients, and shut down ray when you initialized it.
5. **Verify install performance state**: use `from pymoo.functions import
   is_compiled` to check whether Cython-compiled functions are available. Pure
   Python fallback is valid but can be slower.
6. **Control long-run overhead**: set `seed=...` for reproducibility; keep
   `verbose`/progress off for timing; avoid `save_history=True` unless history is
   required because it stores deep copies across generations.

## Open the bundled references

- [Parallelization workflows](references/parallelization-workflows.md): vectorized
  `Problem`, elementwise `StarmapParallelization`, optional joblib/dask/ray, GPU
  patterns, cleanup, and validation.
- [Installation and backends](references/installation-and-backends.md): base vs
  optional extras, compiled-extension checks, backend decision table, and CPU vs
  optional CUDA notes.
- [Troubleshooting](references/troubleshooting.md): slow evaluations, stuck pools,
  pickling failures, missing optional dependencies, unavailable GPU libraries,
  `is_compiled()` surprises, progress overhead, and history memory bloat.

## Bundled scripts

- [scripts/parallel_elementwise_smoke.py](scripts/parallel_elementwise_smoke.py):
  safe CPU-only smoke for `ElementwiseProblem` plus a thread-pool starmap runner.
- [scripts/check_compiled_extensions.py](scripts/check_compiled_extensions.py):
  reports whether compiled pymoo functions are available; use
  `--require-compiled` only when a task explicitly requires compiled speedups.
