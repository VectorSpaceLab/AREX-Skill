# Objective contracts

`scikit-opt` optimizers minimize an objective. Most continuous optimizers and GA-family optimizers call an internal transformer so the optimizer can evaluate a whole population matrix while the user may still write a scalar objective. Shape discipline is the most important reliability rule.

## Scalar objective contract

Use this contract for `common`, `multithreading`, `multiprocessing`, `cached`, and `joblib` run modes.

```python
def objective(x):
    # x is one candidate vector, usually a 1-D numpy array or tuple-like row.
    x0, x1 = x
    return float(x0 * x0 + x1 * x1)
```

Rules:

- Input is one candidate vector of length `n_dim`, not a population matrix.
- Return one finite scalar value. Avoid returning a Python list, a length-`n_dim` vector, a pandas object, or a column matrix.
- Bounds, constraint functions, and route-specific objective details are algorithm-owned concerns; keep this sub-skill focused on objective input/output shape.
- A final optimizer result may expose `best_y` as a one-element numpy array because the internal wrapper evaluates `best_x` as a one-row matrix.

## Vectorized objective contract

Use this contract only with `set_run_mode(func, "vectorization")`.

```python
def objective_vectorized(X):
    # X has shape (population, n_dim).
    x0 = X[:, 0]
    x1 = X[:, 1]
    return x0 * x0 + x1 * x1  # shape: (population,)
```

Rules:

- Input is a 2-D matrix whose rows are candidate vectors.
- Return shape must be exactly one value per row: `(population,)` is safest.
- Do not return `(population, n_dim)`, a scalar aggregated over the whole population, or a transposed shape.
- If an algorithm later reshapes results, a 1-D vector remains the most compatible return form.

## Cached objective contract

Cached mode is for a scalar objective whose candidate values repeat, such as integer GA search spaces or small discrete fixtures.

```python
def objective_cached(x):
    # In cached mode, the wrapper converts each row to tuple(x) before calling.
    x = tuple(float(v) for v in x)
    return float((x[0] - 1) ** 2 + (x[1] - 1) ** 2)
```

Important details:

- The internal cache is built with `functools.lru_cache` and keys candidate rows using `tuple(x)`.
- Your function may receive a tuple rather than a numpy array in cached mode. Convert explicitly if the body expects array methods.
- Tuple elements must be hashable. Numeric scalars are safe; nested arrays, lists, dicts, or object-dtype rows can trigger unhashable-input failures.
- Cache wins when repeated candidates are likely. It can add overhead or memory growth when every candidate is unique.

## Method objectives

Bound methods can be used in common, vectorized, multithreading, and cached modes if their shape contract is still correct.

```python
class Model:
    def __init__(self, scale):
        self.scale = scale

    def objective(self, x):
        return float(self.scale * sum(v * v for v in x))
```

Multiprocessing and joblib add serialization requirements; bound methods, closures, lambdas, local functions, and large object state are common failure points.

## When to set mode

Set the run mode before optimizer construction:

```python
from sko.tools import set_run_mode
from sko.GA import GA

set_run_mode(objective_cached, "cached")
ga = GA(func=objective_cached, n_dim=2, size_pop=6, max_iter=3, lb=[0, 0], ub=[2, 2], precision=1)
```

Constructors wrap `func` immediately, so changing `func.mode` after construction does not rebuild the optimizer's stored wrapper. Reconstruct the optimizer if you need a different mode.

## Cross-skill boundaries

- For GA integer `precision`, bit lengths, and `x2gray` encoding behavior, load `../genetic-algorithms/`.
- For route-cost functions that consume permutation vectors, load `../routing-and-combinatorial/`; this sub-skill only covers the general scalar/vector/cache mechanics.
