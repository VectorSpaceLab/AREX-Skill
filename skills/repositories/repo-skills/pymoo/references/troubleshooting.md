# pymoo Cross-Workflow Troubleshooting

Use this reference for install/import and cross-cutting failures. Route
workflow-specific problems to the nearest sub-skill troubleshooting file.

## Install or import fails

Checklist:
1. Use Python `>=3.10`.
2. Install base pymoo first: `python -m pip install -U pymoo`.
3. If building from source or editable checkout, ensure build tools can compile
   Cython extensions against NumPy.
4. Run a minimal import check:

   ```bash
   python - <<'PY'
   import pymoo
   from pymoo.functions import is_compiled
   print(getattr(pymoo, "__version__", "unknown"), is_compiled())
   PY
   ```

5. If optional imports fail, install only the needed extra instead of `full` by
   default.

## Compiled extensions are unavailable

`from pymoo.functions import is_compiled` reports whether compiled performance
functions are available. Pure Python fallback can still be correct, but may be
slower for non-dominated sorting, decomposition, or related performance-critical
operations.

Recovery options:
- Continue if correctness matters more than speed.
- Reinstall from a wheel or rebuild in an environment with compatible Python,
  NumPy, Cython, and compiler support.
- Use `performance-and-parallelization/scripts/check_compiled_extensions.py` and
  pass `--require-compiled` only when a task explicitly needs compiled speedups.

## Optional dependency is missing

Base pymoo does not guarantee optional packages for every documented extension.
Common optional needs:

| Need | Install direction | Route |
| --- | --- | --- |
| joblib/dask/ray runners | `pymoo[parallelization]` | `performance-and-parallelization` |
| Optuna-backed hyperparameter examples | `optuna` or an optional extras path that includes it | `operators-and-variables` |
| COMO-CMA-ES algorithm | `comocma` | `optimization-workflows` plus optional dependency check |
| recorder/video/live visualization | `pymoo[visualization]` / `pyrecorder` and system video/display support | `analysis-and-visualization` |
| GPU tensor objective | User-chosen torch/JAX/CuPy/CUDA stack | `performance-and-parallelization` |

Do not claim an optional backend is verified unless a task-specific smoke test
has run in the active environment.

## Wrong objective or constraint convention

pymoo minimizes all objectives and treats inequality constraints as `G <= 0`.
If results look inverted or infeasible, read `problem-modeling` before changing
algorithms.

## Optimization result is empty, infeasible, or inconsistent

Likely causes can span several routes:
- Problem output shape/sign/NaN issue -> `problem-modeling`.
- Inadequate algorithm/termination/seed/result interpretation ->
  `optimization-workflows`.
- Invalid variable/operator/repair behavior -> `operators-and-variables`.
- Too-small or slow evaluation budget -> `performance-and-parallelization`.
- Metric or plotting mistake after optimization -> `analysis-and-visualization`.

Start with the smallest built-in problem smoke, then validate the custom problem,
then run the root or sub-skill bundled scripts.

## Headless plotting fails

Matplotlib GUI backends may not work in automated agents. Set a non-interactive
backend before importing pymoo visualization helpers:

```python
import matplotlib
matplotlib.use("Agg")
```

Then call `.save(...)` rather than `.show()`. See the analysis sub-skill's
headless plot script.

## Parallel run hangs

Common causes include unclosed pools, process pickling errors, nested
BLAS/OpenMP oversubscription, objective exceptions swallowed by worker pools, or
running process pools from an interactive context. Read the performance
sub-skill and reduce to a tiny threaded `StarmapParallelization` smoke before
scaling.

## Result analysis metric errors

Hypervolume requires a reference point worse than the points being measured.
GD/IGD/epsilon require a true or accepted approximate Pareto front with matching
objective columns. When no Pareto front is known, prefer hypervolume with an
explicit reference point, non-dominated filtering, or history-based convergence.
