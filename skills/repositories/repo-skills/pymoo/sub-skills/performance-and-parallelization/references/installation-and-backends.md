# Installation and backends

This reference distinguishes base pymoo performance features from optional
parallelization and visualization extras. Do not install or claim optional
backends unless the user asks for them and the task verifies them.

## Base package facts

- Public install command: `pip install -U pymoo`.
- Python requirement: Python 3.10 or newer.
- Base dependencies include NumPy, SciPy, moocore, autograd, cma, matplotlib,
  alive_progress, and Deprecated.
- Base pymoo already supports vectorized `Problem`, sequential elementwise
  evaluation, stdlib thread/process pools through `StarmapParallelization`,
  matplotlib static plotting, and compiled-function detection.
- Base pymoo does **not** guarantee joblib, dask, ray, pyrecorder, optuna,
  comocma, PyTorch, JAX, CuPy, or CUDA runtime packages.

## Optional extras

| Need | Install only if requested | Provides | Do not claim until |
| --- | --- | --- | --- |
| joblib/dask/ray runners | `pip install -U "pymoo[parallelization]"` | `joblib`, `dask[distributed]`, `ray[default]` for optional parallel runners. | Import/construction succeeds in the user's environment. |
| animation/video/live visualization | `pip install -U "pymoo[visualization]"` | `pyrecorder`; static matplotlib plots are already in the base install. | The visualization workflow imports and writes/records successfully. |
| all optional groups | `pip install -U "pymoo[full]"` | Parallelization, optional algorithms/tuning helpers, pyrecorder, and additional heavy packages. | The task explicitly needs broad optional coverage. |
| GPU array backend | User-managed install such as PyTorch, JAX, or CuPy plus compatible device runtime. | Device-side matrix math inside a vectorized `Problem`. | Backend import and device availability are verified. |

Use `pymoo[full]` sparingly: it is broader and heavier than most performance
questions require. Prefer `pymoo[parallelization]` for joblib/dask/ray questions
and base install for stdlib `starmap` or vectorized NumPy workflows.

## Compiled extensions

pymoo can run with pure Python implementations, but selected performance-critical
functions also have Cython-compiled implementations. Check the active install:

```python
from pymoo.functions import is_compiled
print(is_compiled())
```

The bundled helper prints a JSON report and can optionally fail if compiled
extensions are required:

```bash
python scripts/check_compiled_extensions.py
python scripts/check_compiled_extensions.py --require-compiled
```

Interpretation:

- `True`: compiled pymoo functions are available to the active Python process.
- `False`: pymoo should still run, but some operations can fall back to slower
  pure Python implementations.

Compiled functions are used through pymoo's internal function loader for routines
such as non-dominated sorting, decomposition helper calculations, perpendicular
distance, stochastic ranking, nearest-neighbor helpers, and pruning crowding
distance. Future agents usually do not call those compiled modules directly;
they verify `is_compiled()` and then use normal public algorithms and indicators.

## Why installation may be slow or compiled status may be false

On platforms without a compatible prebuilt wheel, installation may compile Cython
extensions. That can require NumPy headers, Cython, and a working C/C++ compiler.
If compilation fails, pymoo may still install and run using pure Python fallback.

Practical response:

1. Do not treat `is_compiled() == False` as a functional install failure unless
   the user explicitly requires compiled speed.
2. If the task is performance-sensitive, ask whether to spend time repairing the
   build toolchain or proceed with pure Python fallback.
3. Re-run the compiled-extension helper after reinstalling or rebuilding.
4. Avoid benchmarking claims until the active install state is verified.

## Backend decision table

| Backend | Base install? | Good for | Main caveat | Cleanup |
| --- | --- | --- | --- | --- |
| Vectorized `Problem` | Yes | NumPy/SciPy batch math, cheap objective functions, GPU array pattern after user installs backend. | Requires writing `_evaluate` over an `(n, n_var)` matrix. | None beyond normal Python resources. |
| Sequential `ElementwiseProblem` | Yes | Debugging a scalar objective before parallelizing. | One candidate at a time; slow for expensive simulations. | None. |
| `StarmapParallelization(ThreadPool(...).starmap)` | Yes | I/O, subprocess calls, NumPy/C-extension work, unpicklable state. | GIL limits pure-Python compute. | `close()` + `join()` or `terminate()` on failure. |
| `StarmapParallelization(multiprocessing.Pool(...).starmap)` | Yes | Heavy pure-Python objectives that are picklable. | Serialization overhead; needs importable top-level classes/functions. | `close()` + `join()` or `terminate()` on failure. |
| `JoblibParallelization` | No; optional `parallelization` extra | Flexible local backends, batching, timeouts, memmap controls. | Optional import; process backends still need serializable state. | Managed internally per call; release external resources you create. |
| `DaskParallelization` | No; optional `parallelization` extra | Existing dask clusters or distributed evaluation. | Workers need imports/data; scheduler overhead can dominate small evaluations. | `client.close()` if created by the script. |
| `RayParallelization` | No; optional `parallelization` extra | Existing ray runtime or resource-aware tasks. | Serialization/object-store overhead; ray must be installed and initialized. | `ray.shutdown()` if initialized by the script. |
| GPU vectorized evaluation | No; user-managed backend | Large matrix/tensor objectives. | Backend and CUDA/device runtime are outside base pymoo; CPU-device copies can dominate. | Release backend resources as appropriate. |

## CPU vs optional CUDA note

A visible GPU device is not enough to claim GPU verification. Future agents must
verify the selected backend import and device probe, for example PyTorch's
`torch.cuda.is_available()` or the equivalent for the chosen library. Without a
verified backend, keep GPU guidance as an optional pattern and use CPU-only
vectorized or starmap helpers for base validation.

When the user asks for CUDA or GPU work:

1. Ask which backend they want or inspect the environment if permitted.
2. Confirm that backend imports and sees the intended device.
3. Keep pymoo outputs as CPU NumPy arrays.
4. Benchmark CPU vectorized vs GPU vectorized on a representative batch; small
   transfers can make GPU slower.

## Minimal import checks

Base starmap:

```python
from multiprocessing.pool import ThreadPool
from pymoo.parallelization.starmap import StarmapParallelization

pool = ThreadPool(2)
try:
    runner = StarmapParallelization(pool.starmap)
finally:
    pool.close()
    pool.join()
```

Joblib optional:

```python
from pymoo.parallelization.joblib import JoblibParallelization
runner = JoblibParallelization(n_jobs=2, backend="threading")
```

Dask optional:

```python
from dask.distributed import Client
from pymoo.parallelization.dask import DaskParallelization
client = Client()
runner = DaskParallelization(client)
client.close()
```

Ray optional:

```python
import ray
from pymoo.parallelization.ray import RayParallelization
ray.init(ignore_reinit_error=True)
runner = RayParallelization(job_resources={"num_cpus": 1})
ray.shutdown()
```
