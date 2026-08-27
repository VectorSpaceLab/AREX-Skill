# Acceleration and optional dependency modes

`set_run_mode(func, mode)` stores the requested mode on the function object. Optimizer constructors then call the package's function transformer and keep the resulting population evaluator. Set the mode first, then construct the optimizer.

## Valid run modes

| Mode | Objective shape | Extra dependency | Good fit | Caveats |
| --- | --- | --- | --- | --- |
| `common` | scalar: one vector -> scalar | none | default, simplest correctness baseline | slowest for costly objectives because rows are evaluated serially |
| `vectorization` | vectorized: matrix -> one value per row | none beyond numpy-style vector operations | fastest when the objective can evaluate all candidates at once | function must return shape `(population,)`; scalar objectives will fail |
| `multithreading` | scalar | standard library threads | I/O-heavy or releasing-GIL objectives; safe smoke alternative to processes | `n_processes=0` lets the thread pool choose its default; thread-safety is the user's responsibility |
| `multiprocessing` | scalar | standard library processes | expensive top-level pure-Python functions on platforms where process pools are safe | requires picklable top-level functions and import-safe `if __name__ == "__main__"` guards in scripts; Windows falls back to threading in mode setup |
| `cached` | scalar, cacheable candidate rows | standard library `lru_cache` | repeated discrete/integer candidates, small search spaces | rows are converted with `tuple(x)`; nested unhashable elements fail; cache can grow |
| `joblib` | scalar | optional `joblib` package | user-managed parallel workflows where joblib is already installed | raises `ImportError` if `joblib` is missing; serialization caveats still apply |
| `parallel` | scalar | standard library threads | legacy spelling only | mode setup rewrites it to `multithreading` and emits a warning |

The transformer also recognizes an internal/default `others` state, which behaves like common scalar row-by-row evaluation. Prefer explicit `common` for clarity in reusable code.

## `n_processes` behavior

Algorithms that expose `n_processes` pass it to the internal transformer. In thread/process modes:

- `n_processes=0` asks the pool implementation to choose its default size.
- A positive integer fixes the pool size.
- Negative values fail an assertion.

For small smoke tests, use `multithreading` with a small positive `n_processes` if you need predictable resource use. Do not use multiprocessing as a default smoke because child-process startup, function pickling, and notebook/import-main behavior are platform-sensitive.

## Choosing a mode

1. Start with `common` until the objective is correct and finite.
2. If the objective is naturally numpy-vectorizable, implement the matrix contract and switch to `vectorization`.
3. If candidates repeat because of integer precision or a small combinatorial space, try `cached`.
4. Use `multithreading` only when the objective is thread-safe and has enough I/O or external wait time to benefit.
5. Use `multiprocessing` or `joblib` only in a normal Python module/script with import-safe top-level functions, explicit resource limits, and a recovery plan for serialization errors.

## Method-based objectives

Bound methods can be assigned a mode, but process-based execution may need the object instance to be picklable. If a method captures large model/data state, prefer `common`, `vectorization`, or a small `multithreading` pool unless the process-serialization path is explicitly tested.

## Optional plotting and data dependencies

Core `sko` optimization does not need plotting. Many demonstration workflows build pandas DataFrames and matplotlib plots after optimization. Treat these as optional presentation dependencies:

- Install or import `pandas` only when tabular history analysis is required.
- Install or import `matplotlib` only when plotting is required.
- In headless environments, select a non-interactive backend before importing pyplot, for example `matplotlib.use("Agg")`, or skip plotting entirely.

Bundled smoke scripts for this skill intentionally avoid pandas, matplotlib, display backends, and data files.

## Optional PyTorch / CUDA `GA.to(device)`

`GA.to(device)` attempts to switch selected GA chromosome operators to PyTorch-backed implementations. It is optional and experimental:

- It imports `torch` lazily. If PyTorch is missing, the method prints a message and returns the GA object without proving GPU acceleration.
- Passing a CUDA device only works when PyTorch, CUDA runtime, drivers, and a CUDA-capable device are available.
- The objective function is still called with CPU/numpy candidate arrays after chromosome conversion, so `GA.to(device)` does not make an arbitrary objective a torch function.
- Missing CUDA or torch is non-blocking for core objective/run-mode use. Fall back to CPU GA or omit `.to(device)`.

For GA precision and integer encoding details that affect repeated candidates and cache usefulness, load `../genetic-algorithms/`.
