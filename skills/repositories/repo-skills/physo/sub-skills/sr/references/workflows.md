# Single-dataset SR workflows

## Route and data contract

Use this route when there is exactly one dataset and one target vector:

```text
X.shape == (n_dim, n_samples)
y.shape == (n_samples,)
```

A common tabular layout is `(n_samples, n_dim)`; transpose it before calling
`physo.SR`. Values must be float32/float64-convertible and must not contain
NaNs. If the user has several related realizations, per-realization constants,
or a request for one common form across datasets, route to `class-sr` instead
of concatenating unrelated data.

A preflight block that catches most shape mistakes:

```python
import numpy as np

X = np.asarray(X, dtype=float)
y = np.asarray(y, dtype=float)
assert X.ndim == 2, "X must be (n_dim, n_samples)"
assert y.ndim == 1, "y must be (n_samples,)"
assert X.shape[1] == y.shape[0], "X and y must share n_samples"
assert np.isfinite(X).all() and np.isfinite(y).all()
```

## Safe quick start

The bundled [`../scripts/smoke_sr_quick_start.py`](../scripts/smoke_sr_quick_start.py)
runs a tiny CPU-only weighted SR call and reloads the Pareto pkl it creates in
a scratch directory. It defaults to `config0` and accepts `--preset config0b`
for the longer free-constant-optimization variant. It is intentionally shorter
than full demos and benchmark runners: use it as an installed-package smoke,
not as a scientific hyperparameter setting.

Minimal structure for an experiment adapted from the canonical quick start:

```python
import copy
import numpy as np
import torch
import physo
import physo.learn.monitoring as monitoring

np.random.seed(0)
torch.manual_seed(0)

x0 = np.linspace(-1.0, 1.0, 32)
x1 = np.linspace(0.2, 1.2, 32)
X = np.stack((x0, x1), axis=0)
y = 0.75*x0 + 0.25*x1**2

y_weights = np.ones_like(y)
y_weights[len(y)//2:] = 4.0

run_config = copy.deepcopy(physo.config.config0.config0)
run_logger = lambda: monitoring.RunLogger(save_path="sr.log", do_save=True)
run_visualiser = lambda: monitoring.RunVisualiser(
    save_path="sr_curves.png", do_show=False, do_prints=True, do_save=True
)

expression, logs = physo.SR(
    X, y,
    y_weights=y_weights,
    X_names=["x0", "x1"],
    X_units=[[0, 0, 0], [0, 0, 0]],
    y_name="y",
    y_units=[0, 0, 0],
    fixed_consts=[1.0],
    fixed_consts_units=[[0, 0, 0]],
    free_consts_names=["a", "b"],
    free_consts_units=[[0, 0, 0], [0, 0, 0]],
    run_config=run_config,
    get_run_logger=run_logger,
    get_run_visualiser=run_visualiser,
    parallel_mode=False,
    device="cpu",
    epochs=5,
)
```

For a notebook or smoke, keep `parallel_mode=False`. For a longer Python script
on CPU, `parallel_mode=True` and `n_cpus=<count>` may help free-constant
optimization, but test it on the target machine because process overhead can
dominate small datasets.

## Dimensional-analysis workflow

PhySO can use physical units to restrict the search space. Units are vectors of
consistent component order and width across all variables and constants, with a
maximum width of seven. The order is user-defined; `[length, time, mass]` and
`[mass, time, length]` are both valid conventions if every vector uses the same
one.

Example based on the SR quick-start energy problem:

```python
X_names = ["z", "v"]
X_units = [[1, 0, 0], [1, -1, 0]]  # z: L, v: L/T
y_name = "E"
y_units = [2, -2, 1]               # energy: L^2/T^2*M
fixed_consts = [1.0]
fixed_consts_units = [[0, 0, 0]]
free_consts_names = ["m", "g"]
free_consts_units = [[0, 0, 1], [1, -2, 0]]
```

If the problem is not dimensioned, omit the unit arguments or pass zero vectors
of the same width. Missing units are treated as dimensionless and can produce
warnings. Do not mix vector widths, and give exactly one unit row per input
variable, fixed constant, and free constant.

The default `config0`/`config0b` families include `PhysicalUnitsPrior`, so
consistent units are used automatically when provided.

## Weighted-data workflow

`y_weights` can be a scalar or a per-sample vector aligned with `y`. The weights
are used during free-constant optimization and reward computation, so they
change which parts of the dataset the search prioritizes. The SR weights demo
uses the pattern below to make late samples dominate a one-dimensional signal:

```python
t = np.random.uniform(0.1, 10.0, 1000)
X = np.stack((t,), axis=0)
y = np.exp(-1.45*t) + 0.5*np.cos(3.7*t)
y_weights = 0.01 + (t > 5.0).astype(float)
```

Use weights for uncertainty or intentional emphasis, not as a substitute for
removing invalid rows. Very small or very large weights can make the result look
as if the unweighted region was ignored; normalize or rescale when that is not
intended.

## Candidate-wrapper workflow

`candidate_wrapper` is optional. It receives a candidate callable and `X`, then
returns the wrapped prediction. Keep it differentiable and written with torch
operations if free constants are optimized.

```python
def identity_wrapper(func, X):
    return func(X)

expression, logs = physo.SR(
    X, y,
    candidate_wrapper=identity_wrapper,
    parallel_mode=False,
)
```

When using multiprocessing, define the wrapper at module top level rather than
as a lambda or nested function so it is picklable. The wrapper must preserve the
sample axis expected by the reward function.

## Result and Pareto inspection

The return value is `(expression, logs)`:

```python
print(expression.get_infix_pretty())
print(expression.get_infix_sympy())
print(expression.get_infix_sympy(evaluate_consts=True)[0])
complexities, programs, rewards, rmse = logs.get_pareto_front()
```

For saved runs, `RunVisualiser(save_path="sr_curves.png", do_save=True)` writes
files such as `sr_curves_pareto.pkl` and `sr_curves_pareto.csv`.

```python
pareto_programs = physo.read_pareto_pkl("sr_curves_pareto.pkl")
best_program = pareto_programs[-1]

# For ordinary SR without realization-specific constants, CSV loading returns
# SymPy expressions with constants evaluated.
sympy_exprs, pareto_df = physo.read_pareto_csv(
    "sr_curves_pareto.csv", return_df=True
)
```

Use `physo.load_expr(path)` for an individual `Program` saved with
`Program.save(path)`. Route low-level expression manipulation, custom library
building, and random-expression sampling to the toolkit sibling.

## Scope notes

The bundled helper is a compact quick-start pattern. Weighted-data guidance is
kept as reference material rather than a long interactive workflow. Long
benchmark runners and job-file generators are maintainer automation and are not
SR runtime helpers.
