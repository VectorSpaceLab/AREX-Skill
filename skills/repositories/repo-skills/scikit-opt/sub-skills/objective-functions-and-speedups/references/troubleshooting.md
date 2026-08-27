# Troubleshooting objective functions and speedups

## Mode name assertion

Symptom: construction or first evaluation fails with an assertion mentioning valid modes.

Likely causes:

- Typo such as `threading`, `multi-threading`, `vectorized`, or `cache`.
- A custom attribute `func.mode` was set to an unsupported value.

Fix:

```python
from sko.tools import set_run_mode
set_run_mode(func, "vectorization")  # or common, multithreading, multiprocessing, cached, joblib
```

Remember that legacy `parallel` is only an alias: it is rewritten to `multithreading` and emits a warning.

## Mode set too late

Symptom: changing the mode appears to do nothing.

Cause: optimizers wrap the objective during construction.

Fix: call `set_run_mode(func, mode)` before constructing the optimizer, or reconstruct the optimizer after changing the mode.

## Vectorized shape errors

Symptoms:

- `IndexError` from using `p[:, 0]` on a scalar candidate vector.
- `TypeError` or unpacking errors from using `x0, x1 = X` on a population matrix.
- Returned values have shape `(population, n_dim)`, `(population, 1)` when downstream code expects 1-D, or a single scalar for the whole population.

Fix:

```python
def objective_vectorized(X):
    X = np.asarray(X, dtype=float)
    values = X[:, 0] ** 2 + X[:, 1] ** 2
    return np.asarray(values, dtype=float).reshape(-1)
```

If the objective is not truly vectorized, remove vectorization mode and use `common` until the scalar contract passes.

## Cached input errors

Symptoms:

- `TypeError: unhashable type` from cached mode.
- Attribute errors because the objective expected numpy array methods but received a tuple.
- Cache mode is slower or memory grows unexpectedly.

Causes and fixes:

- Cached mode calls the scalar objective with `tuple(x)`. Convert at the start of the function if needed: `x = np.asarray(x, dtype=float)`.
- Candidate tuple elements must be hashable numeric values. Avoid object-dtype rows, nested arrays, lists, or dicts.
- Use cached mode mainly for integer/discrete search spaces with repeated candidates. For high-precision continuous spaces, prefer vectorization or common mode.

## Multithreading problems

Symptoms: nondeterministic results, shared-state corruption, or no speedup.

Fixes:

- Keep objective functions pure when possible.
- Avoid mutating shared global state, open handles, random generators, or model objects without locks.
- Use a small positive `n_processes` for predictable resource use.
- If the objective is CPU-bound Python code that does not release the GIL, threads may not improve speed.

## Multiprocessing pickling and import-main issues

Symptoms:

- Pickling errors for local functions, lambdas, closures, bound methods, or large captured objects.
- Child processes recursively start work or hang in notebooks/interactive shells.
- Platform-specific fallback or warning on Windows.

Fixes:

- Put the objective at module top level.
- Protect script entry points with `if __name__ == "__main__":`.
- Avoid closures and unpicklable objects; pass small immutable configuration instead.
- Test a tiny process run before expensive optimization.
- Prefer `multithreading` or `common` for bundled smoke checks and interactive contexts.

## Joblib ImportError or serialization errors

Symptoms: `ImportError: No module named joblib`, pickling errors, or worker crashes after selecting `joblib`.

Fixes:

- Treat `joblib` as optional. Install it only if the task explicitly needs that mode.
- Keep the objective top-level and picklable, just as for multiprocessing.
- Fall back to `common`, `vectorization`, or `multithreading` if joblib is not part of the environment.

## Optional `GA.to(device)` torch/GPU issues

Symptoms:

- A message that PyTorch is needed.
- CUDA device requested but unavailable.
- The objective still receives numpy arrays rather than torch tensors.

Fixes:

- Treat `GA.to(device)` as optional and experimental, not required for core optimization.
- Check `torch.cuda.is_available()` before choosing a CUDA device.
- Use CPU GA when torch or CUDA is unavailable.
- Do not rewrite the objective as torch-only unless you have separately verified the actual values passed to it.

## Matplotlib display problems

Symptoms: display/backend errors, windows opening in automation, or hangs around plotting.

Fixes:

- Keep optimization scripts headless and omit plotting during smoke checks.
- If plotting is required, set a non-interactive backend before importing pyplot:

```python
import matplotlib
matplotlib.use("Agg")
```

- Treat `pandas` and `matplotlib` as optional example/reporting dependencies, not core `sko` requirements.

## TSP and `PSO_TSP` caveat

Route-cost objectives and permutation validation belong to the routing sub-skill. Do not infer that every objective run mode applies to every route optimizer. In the verified package version for this skill, constructing `PSO_TSP` raised a `TypeError` because its call to the function transformer omitted the required process-count argument; use routing alternatives documented by the routing sub-skill rather than claiming `PSO_TSP` works.
