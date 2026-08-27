# Troubleshooting performance and parallelization

Use this reference when a pymoo run is slow, workers hang, optional backends fail,
compiled extensions are missing, GPU libraries are unavailable, or long runs use
unexpected memory.

## Slow objective evaluations

Symptoms:

- More workers do not improve `res.exec_time`.
- CPU usage is low or uneven.
- A parallel version is slower than a sequential/vectorized version.

Likely causes and fixes:

1. **Objective is too cheap for parallelism**: worker scheduling dominates.
   Prefer vectorized `Problem`, increase batch size only if the model really
   needs it, or stay sequential.
2. **Python loop inside vectorized `_evaluate`**: rewrite math with NumPy/SciPy
   matrix operations when possible.
3. **Too many workers**: BLAS/OpenMP libraries may already spawn threads. Try a
   smaller worker count before using all cores.
4. **`verbose` or progress overhead**: set `verbose=False` and avoid progress
   bars during timing runs.
5. **Random simulation noise**: repeated timing can be unstable if the objective
   uses unseeded randomness. Make the simulation deterministic or seed it
   explicitly.

Quick diagnostic:

```python
res = minimize(problem, algorithm, ("n_gen", 3), seed=1, verbose=False)
print(res.exec_time, res.algorithm.evaluator.n_eval)
```

Compare a vectorized version, sequential elementwise version, and the selected
parallel runner on the same tiny termination budget.

## Pool does not close or process stays alive

Symptoms:

- Script reaches the end but the shell prompt does not return.
- Interrupting leaves worker processes behind.
- A notebook/kernel or test process hangs after a parallel run.

Fixes:

- Always call `close()` and `join()` for successful pool runs.
- Use `terminate()` and `join()` if evaluation raises an exception.
- For process pools, run from a script with `if __name__ == "__main__":` so
  worker startup does not recursively execute the script.
- Avoid creating pools at import time. Create them in a function or main block.
- Close dask clients and shut down ray only if the script initialized them.

Safe pattern:

```python
pool = ThreadPool(4)
try:
    runner = StarmapParallelization(pool.starmap)
    # construct ElementwiseProblem(elementwise_runner=runner) and run pymoo
except BaseException:
    pool.terminate()
    pool.join()
    raise
else:
    pool.close()
    pool.join()
```

## Process pickling errors

Symptoms:

- `Can't pickle ...` errors from multiprocessing/joblib/dask/ray.
- Worker cannot import the problem class or simulation function.
- Process workers crash before evaluating any candidate.

Fixes:

- Define problem classes and worker functions at module top level.
- Avoid lambdas, nested functions, generators, open file handles, live sockets,
  loggers with unpicklable handlers, and large mutable objects captured by
  closures.
- Keep data references small; load large read-only data inside each worker or use
  a backend-specific shared/memmap mechanism.
- If the simulation is unpicklable but releases the GIL or is I/O-bound, switch
  to `ThreadPool` or joblib `backend="threading"`.
- If the simulation must use processes, build a tiny standalone script that
  imports the problem and evaluates one candidate before running pymoo.

## Optional dependency import failure

Symptoms:

- `ImportError: joblib must be installed` when constructing
  `JoblibParallelization`.
- `ModuleNotFoundError: No module named 'dask'` or `No module named 'ray'`.
- A task assumes optional visualization animation support but `pyrecorder` is
  missing.

Fixes:

1. Confirm the user wants optional dependencies installed.
2. For joblib/dask/ray, install the parallelization extra instead of broad extras
   unless broader coverage is needed: `pip install -U "pymoo[parallelization]"`.
3. For animation/video/live visualization, install `pymoo[visualization]` only
   when those features are required.
4. Do not use `pymoo[full]` unless the user explicitly needs all optional groups.
5. Fall back to base stdlib `StarmapParallelization` when optional packages are
   not available and the task can run locally.

## GPU or CUDA backend not available

Symptoms:

- `ModuleNotFoundError` for torch, jax, or cupy.
- GPU device probe returns false.
- GPU version runs slower than CPU.
- pymoo receives a backend tensor instead of a NumPy array.

Fixes:

- Treat GPU as optional and unverified until the selected backend imports and
  reports the intended device.
- Keep the base solution CPU-only unless the user asks for GPU and accepts the
  backend install/verification cost.
- In vectorized GPU problems, convert input NumPy arrays to device arrays inside
  `_evaluate`, compute, then assign CPU NumPy arrays to `out["F"]`, `out["G"]`,
  and `out["H"]` as needed.
- Benchmark with representative batch sizes. Device transfer overhead can erase
  benefits for small populations or cheap objectives.
- For JAX float64-sensitive problems, enable float64 configuration before
  evaluation.

## `is_compiled()` is false or install is slow

Symptoms:

- `from pymoo.functions import is_compiled; is_compiled()` returns `False`.
- Installation spends time compiling Cython extensions.
- Runtime warning says compiled modules are unavailable and pure Python fallback
  is being used.

Meaning:

- pymoo can still run without compiled modules.
- Performance-sensitive internals can be slower in pure Python fallback.
- A failed or skipped Cython build is an install-performance issue, not
  automatically a package import failure.

Fixes:

1. Use `scripts/check_compiled_extensions.py` to report the active state.
2. If compiled speed is required, ensure a compiler, Cython, and compatible NumPy
   build headers are available, then reinstall/rebuild pymoo.
3. If the task only needs correctness or small smoke tests, proceed with pure
   Python fallback and state that compiled speedups were not verified.
4. Avoid comparing performance against compiled runs unless both environments
   report the same compiled-extension state.

## Memory or history bloat

Symptoms:

- Long runs grow memory each generation.
- Results are large when `res.history` is populated.
- Dask/ray object stores or process workers consume more memory than expected.

Fixes:

- Keep `save_history=False` unless convergence analysis explicitly needs the
  full history.
- If history is required, reduce population size/generation count for debugging
  or store only scalar metrics in a callback.
- Avoid attaching large arrays, simulator handles, or datasets to the algorithm
  object when `save_history=True`, because algorithm snapshots can retain them.
- For distributed backends, release worker-side objects and close the scheduler
  resources after the run.
- Route Pareto-front metrics and plotting from saved history to the
  analysis-and-visualization sub-skill.

## Reproducibility surprises

Symptoms:

- Runs with the same pymoo `seed` differ unexpectedly.
- Parallel objective calls produce non-repeatable simulation values.
- Job scheduling order changes results.

Fixes:

- Always pass `seed=...` to `minimize` or set the algorithm seed before setup.
- Do not use global unseeded random generators inside `_evaluate`.
- For stochastic simulations, derive per-candidate seeds from deterministic
  inputs or from an explicit seed schedule stored outside worker-global state.
- Avoid relying on process scheduling order for random draws.
- Keep parallel workers side-effect free whenever possible.

## When to route away

- Wrong `F`, `G`, or `H` shapes; sign conventions; bounds; NaN replacement;
  vectorized vs elementwise problem definitions: route to problem-modeling.
- Termination not found, algorithm not converging, ask-and-tell execution, or
  result fields: route to optimization-workflows.
- Hypervolume/GD/IGD, reference directions, convergence plots, or headless
  plotting: route to analysis-and-visualization.
