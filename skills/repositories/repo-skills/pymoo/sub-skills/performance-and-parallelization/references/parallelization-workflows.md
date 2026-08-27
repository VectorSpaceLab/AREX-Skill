# Parallelization workflows

This reference helps choose and implement pymoo evaluation acceleration without
assuming optional packages or GPU libraries. The key design choice is whether the
objective can be evaluated as a matrix or only one candidate at a time.

## Decision workflow

| Situation | Preferred pattern | Why | Validate with |
| --- | --- | --- | --- |
| Objective is NumPy/SciPy math over many candidates | Vectorized `Problem` | Avoids Python scheduling, pickling, and worker startup overhead. | Compare `res.exec_time`, check finite `res.F`, assert expected evaluation count. |
| Objective calls one expensive simulation per candidate | `ElementwiseProblem(elementwise_runner=...)` | Lets pymoo distribute element evaluations while preserving pymoo's algorithm loop. | Tiny run with fixed `seed`, low generations, and explicit cleanup. |
| Objective releases the GIL or waits on I/O/subprocesses | Thread pool `starmap` | Low overhead, shared memory, fewer pickle constraints. | Use `ThreadPool`, close/join, inspect no hanging workers. |
| Heavy pure-Python objective and picklable state | Process pool or joblib process backend | Runs Python bytecode on separate cores, but pays serialization cost. | Run from a script guarded by `if __name__ == "__main__"`. |
| Cluster/distributed execution already exists | dask or ray runner | Uses external scheduler/resources. Requires optional dependencies and explicit lifecycle management. | Prove worker imports and close scheduler resources. |
| Matrix code already has a torch/JAX/CuPy implementation | Optional GPU vectorized `Problem` | Can accelerate large batched math if transfer costs are small. | Verify backend import and device availability; return CPU NumPy arrays to pymoo. |

For very cheap objectives, parallelism can be slower than sequential/vectorized
execution. Benchmark a tiny representative run before increasing population size
or generation count.

## Vectorized `Problem` first

Use a vectorized problem when `_evaluate` can process all candidates in one array.
`X` has shape `(n_candidates, n_var)` and outputs should be one value per row.

```python
import numpy as np
from pymoo.core.problem import Problem

class SphereBatch(Problem):
    def __init__(self):
        super().__init__(n_var=10, n_obj=1, n_ieq_constr=0, xl=-5.0, xu=5.0)

    def _evaluate(self, X, out, *args, **kwargs):
        out["F"] = np.sum(X ** 2, axis=1, keepdims=True)
```

Operational notes:

- Vectorization is usually fastest for NumPy/SciPy-heavy objectives.
- Keep output shape explicit. For one objective, `(n_candidates, 1)` is safest;
  many pymoo examples also use a one-dimensional vector for one objective.
- Detailed objective/constraint shape modeling belongs in the problem-modeling
  sub-skill; keep this sub-skill focused on evaluation throughput.
- Time vectorized, sequential elementwise, and parallel elementwise variants on a
  small problem before scaling.

## Elementwise starmap runner

Use `ElementwiseProblem` when each candidate is evaluated by an expensive
black-box call. The runner receives pymoo's elementwise evaluation function and
an iterable of candidate vectors.

```python
from multiprocessing.pool import ThreadPool
import numpy as np
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.parallelization.starmap import StarmapParallelization

class ExpensiveScalarProblem(ElementwiseProblem):
    def __init__(self, **kwargs):
        super().__init__(n_var=6, n_obj=1, n_ieq_constr=0, xl=-2.0, xu=2.0, **kwargs)

    def _evaluate(self, x, out, *args, **kwargs):
        # Replace this with one deterministic simulation call.
        out["F"] = float(np.sum((x - 0.25) ** 2))

pool = ThreadPool(4)
try:
    runner = StarmapParallelization(pool.starmap)
    problem = ExpensiveScalarProblem(elementwise_runner=runner)
    res = minimize(problem, GA(pop_size=20), ("n_gen", 5), seed=1, verbose=False)
    assert res.F is not None
finally:
    pool.close()
    pool.join()
```

Thread/process choice:

- Threads are good for NumPy/C-extension work, external I/O, subprocess-backed
  simulations, and unpicklable Python objects. They share memory but Python code
  still has the GIL.
- Processes are good for heavy pure-Python work that can be serialized. Define
  the problem class and simulation function at module top level, avoid lambdas
  and open handles, and run from a normal Python script.
- With processes, use the script pattern:

```python
import multiprocessing as mp
from pymoo.parallelization.starmap import StarmapParallelization

if __name__ == "__main__":
    pool = mp.Pool(4)
    try:
        runner = StarmapParallelization(pool.starmap)
        # construct problem and run minimize(...)
    finally:
        pool.close()
        pool.join()
```

If an exception happens inside worker evaluation, terminate the pool instead of
waiting forever:

```python
pool = ThreadPool(4)
try:
    # run pymoo
    pass
except BaseException:
    pool.terminate()
    pool.join()
    raise
else:
    pool.close()
    pool.join()
```

## Optional joblib runner

`JoblibParallelization` is an optional runner. Do not assume it exists in a base
install; install the parallelization extra only when the user asks for it.

```python
from pymoo.parallelization.joblib import JoblibParallelization

runner = JoblibParallelization(n_jobs=4, backend="threading")
problem = ExpensiveScalarProblem(elementwise_runner=runner)
```

Useful joblib choices:

- `backend="threading"`: low overhead; best when the objective releases the GIL
  or waits on I/O.
- `backend="loky"`: default robust process backend; best for picklable pure
  Python work.
- `backend="multiprocessing"`: process backend with different trade-offs; still
  requires picklable state.
- `n_jobs=-1`: use all cores; prefer a fixed smaller value in shared systems or
  when BLAS/OpenMP libraries already spawn threads.
- `batch_size="auto"`, `pre_dispatch="2*n_jobs"`, and `timeout=...` can help for
  large or uneven tasks.

## Optional dask runner

Use dask only when the task already has a dask distributed client or explicitly
needs distributed scheduling. Close the client you create.

```python
from dask.distributed import Client
from pymoo.parallelization.dask import DaskParallelization

client = Client(processes=True)
try:
    runner = DaskParallelization(client)
    problem = ExpensiveScalarProblem(elementwise_runner=runner)
    # run minimize(...)
finally:
    client.close()
```

Dask workers must be able to import the problem class and every dependency used
by `_evaluate`. Large captured objects can dominate runtime through scheduler and
serialization overhead.

## Optional ray runner

Use ray only when ray is installed and initialized for the task. Shut ray down if
you initialized it in the same script.

```python
import ray
from pymoo.parallelization.ray import RayParallelization

ray.init(ignore_reinit_error=True)
try:
    runner = RayParallelization(job_resources={"num_cpus": 1})
    problem = ExpensiveScalarProblem(elementwise_runner=runner)
    # run minimize(...)
finally:
    ray.shutdown()
```

Ray serializes the elementwise evaluation callable and candidate data. Keep
problem state small, importable, and deterministic.

## Optional GPU vectorized pattern

pymoo's base install does not provide a CUDA/PyTorch/JAX/CuPy stack. GPU support
is a user-supplied backend pattern: convert pymoo's NumPy batch to a device array,
compute batched objectives, then return CPU NumPy arrays in `out`.

PyTorch-style sketch:

```python
import numpy as np
import torch
from pymoo.core.problem import Problem

class TorchBatchProblem(Problem):
    def __init__(self):
        super().__init__(n_var=10, n_obj=1, xl=-5.0, xu=5.0)

    def _evaluate(self, X, out, *args, **kwargs):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        X_t = torch.as_tensor(X, dtype=torch.float64, device=device)
        F_t = torch.sum(X_t ** 2, dim=1, keepdim=True)
        out["F"] = F_t.detach().cpu().numpy()
```

Caveats:

- Do not claim GPU acceleration unless the task verifies backend import and
  device availability.
- Transfer costs can dominate small batches; GPU is most useful for large
  batched math.
- Return plain NumPy arrays to pymoo.
- For JAX, enable float64 explicitly if the optimization depends on float64
  precision.

## Reproducibility and overhead controls

- Pass `seed=...` to `minimize` or set the algorithm seed before setup.
- Custom objective code should avoid global unseeded random draws; seed any
  simulation randomness from explicit inputs or task-controlled seeds.
- Set `verbose=False` and avoid progress bars while benchmarking raw evaluation
  speed. Progress display uses `alive_progress` and can add terminal overhead.
- Leave `save_history=False` unless later analysis explicitly needs it. Enabling
  history stores algorithm snapshots across generations and can consume a lot of
  memory for large populations or large objects attached to the algorithm.
- Avoid oversubscription: if NumPy/BLAS already uses many threads, using many
  pymoo workers can slow the run. Start with a small worker count.

## Final validation checklist

Before handing a parallel pattern to a future agent:

1. Run a tiny deterministic smoke with the same runner type.
2. Assert `res.F` is present and finite.
3. Inspect `res.algorithm.evaluator.n_eval` to confirm evaluations actually ran.
4. Confirm every pool/client/scheduler is closed after the run.
5. Record whether optional dependencies or GPU libraries were verified; if not,
   keep them documented as optional and unverified.
