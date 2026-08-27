# SR troubleshooting

## Import and dependency checks

A minimal installed-package check should import the public API and scientific
runtime dependencies:

```bash
python - <<'PY'
import physo, torch, numpy, sympy, pandas, matplotlib, sklearn
print("physo", getattr(physo, "__version__", "unknown"))
print("cuda available", torch.cuda.is_available())
for name in ["SR", "ClassSR", "read_pareto_csv", "read_pareto_pkl", "load_expr"]:
    assert hasattr(physo, name), name
PY
python -m pip check
```

The verified minimum environment for this skill is CPU-only and includes
`physo`, PyTorch CPU, NumPy, SymPy, pandas, matplotlib, and scikit-learn. A
warning about missing system LaTeX at import/display time is expected when LaTeX
is not installed and is not an SR failure.

## `X` / `y` shape mismatch

Symptom examples:

- `X must have shape = (n_dim, data_size,)`
- `y must have shape = (data_size,)`
- `X must have shape = (n_dim, data_size,) and y must have shape = (data_size,) with the same data_size.`

Recovery:

```python
X = np.asarray(X, dtype=float)
y = np.asarray(y, dtype=float)
if X.ndim == 2 and X.shape[0] == y.shape[0] and X.shape[1] != y.shape[0]:
    X = X.T  # likely had (n_samples, n_dim)
assert X.ndim == 2 and y.ndim == 1
assert X.shape[1] == y.shape[0]
assert np.isfinite(X).all() and np.isfinite(y).all()
```

Do not pass a pandas DataFrame directly unless you explicitly convert and
transpose it. Do not pass Class SR-style lists to `physo.SR`; route multi-
dataset input to the sibling Class SR skill.

## Units length or dimensionality mismatch

PhySO checks that every named input, fixed constant, and free constant has one
unit row. It also expects `y_units` to be a one-dimensional vector. Frequent
mistakes:

- `len(X_names) != len(X_units)` or `len(X_names) != X.shape[0]`;
- `free_consts_names` has two names but `free_consts_units` has one row;
- `y_units` is nested like `[[0, 0, 0]]` instead of `[0, 0, 0]`;
- variable vectors use different conventions or widths.

Recovery checklist:

```python
assert len(X_names) == X.shape[0]
assert len(X_units) == X.shape[0]
assert np.asarray(y_units).ndim == 1
unit_width = len(y_units)
for row in list(X_units) + list(fixed_consts_units or []) + list(free_consts_units or []):
    assert len(row) == unit_width
```

If the task is dimensionless, omit units or pass zero vectors everywhere. If it
is physical, include units for free constants; those units often make mixed
terms physically valid.

## `y_weights` length or scale mistakes

For `physo.SR`, `y_weights` is either a scalar or a vector of exactly the same
length as `y`. It is not a list of datasets; that is a Class SR pattern.

```python
y_weights = np.asarray(y_weights, dtype=float)
assert y_weights.ndim == 1
assert y_weights.shape == y.shape
assert np.isfinite(y_weights).all()
```

Weights affect free-constant optimization and reward. If high-weight regions are
fit well while low-weight regions degrade, this is expected. If that was not the
intent, normalize weights to a moderate range or remove the weighting.

## `candidate_wrapper` failures

Symptoms include assertion failures that `candidate_wrapper should be callable`,
constant optimization warnings, or shape/device errors during candidate
execution.

Recovery:

- define the wrapper as `def wrapper(func, X): ...`;
- return a torch tensor with the same sample axis expected by `y`;
- use torch operations if free constants are optimized;
- avoid lambdas, nested functions, or non-picklable state when
  `parallel_mode=True`;
- test with an identity wrapper first:

```python
def identity_wrapper(func, X):
    return func(X)
```

If the identity wrapper works but the custom wrapper fails, the issue is in the
wrapper, not in the SR data contract.

## `op_names` and prior mismatch

The config priors are built after the library is created. If you remove
operators that a prior names, PhySO may warn that the prior could not be made or
that a trigonometric prior has no trigonometric tokens. The SR unit tests include
a reduced-operator case and tolerate those warnings.

Recovery choices:

1. Restore the default operator set while debugging.
2. If the reduced grammar is intentional, deep-copy the config and remove or
   adjust priors that reference omitted tokens.
3. Keep `max_time_step` compatible with `HardLengthPrior.max_length`.

Do not interpret every prior warning as a fatal error. Treat it as a sign that
the actual search grammar is different from the preset's intended grammar.

## CPU, CUDA, and `parallel_mode`

This skill is verified only for CPU. For safe execution:

```python
parallel_mode = False
device = "cpu"
n_cpus = 1
```

`parallel_mode=True` is for Python scripts and can be slower on small runs due
to multiprocessing overhead. If a user installs CUDA PyTorch separately,
`device="cuda"` is outside this skill's verification. Do not claim that CUDA was
validated here.

## Missing LaTeX or display extras

Plain string, pretty text, and SymPy inspection do not require system LaTeX.
Warnings such as missing `latex` only affect optional rendering paths such as
LaTeX images or tree displays. Prefer these safe fallbacks:

```python
print(expression.get_infix_str())
print(expression.get_infix_pretty())
print(expression.get_infix_sympy())
```

Install LaTeX/display extras only when the user specifically needs graphical
formula or tree rendering.

## Log and Pareto loading problems

If `physo.read_pareto_pkl("...")` or `physo.read_pareto_csv("...")` fails with
`FileNotFoundError`, the run probably did not save Pareto artifacts. The Pareto
pkl/csv are saved by `RunVisualiser(do_save=True)`, with names derived from the
visualiser `save_path` stem.

```python
run_visualiser = lambda: monitoring.RunVisualiser(
    save_path="run_curves.png",
    do_show=False,
    do_prints=True,
    do_save=True,
)
# produces run_curves_pareto.pkl and run_curves_pareto.csv
```

Immediate in-memory inspection works without saved files:

```python
complexities, programs, rewards, rmse = logs.get_pareto_front()
```

For standard SR outputs, `physo.read_pareto_csv` returns SymPy expressions with
free constants evaluated. For richer `Program` objects and for workflows that
may involve realization-specific constants, prefer `physo.read_pareto_pkl`.

## Fast synthetic checks for future verification

- Weighted-tail check: create a tiny one-dimensional dataset with
  `y_weights = 0.01 + (x > x.mean()).astype(float)` and verify that the skill
  explains how weighting changes the reward rather than promising unweighted
  accuracy.
- Invalid-unit check: provide one `X_units` row for two input variables, or a
  nested `y_units=[[0, 0, 0]]`, and verify that the recovery path points to the
  units-shape contract before changing the search algorithm.
