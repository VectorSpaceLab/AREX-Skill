# Workflow Recipes

This page gives small, safe patterns for the wrapper layer. Use the smoke helper first if you just want a quick import and behavior check.

## 1. NumPy wrapper smoke

Use this when you want a minimal gradient-backed example that exercises ordinary `autograd.numpy` primitives.

```python
import autograd.numpy as np
from autograd import grad


def loss(x):
    return np.sum(np.sin(x) ** 2 + np.maximum(x, 0.0))

x = np.array([-0.5, 0.25, 1.5])
print(grad(loss)(x))
```

What to expect:

- The array stays in `autograd.numpy` the whole time.
- The final result is a scalar, so `grad` can trace it.
- `np.maximum` is a good sanity check for supported piecewise behavior.

## 2. xarray-backed gradient

Use this when a `DataArray` or another `__array_ufunc__` container should carry boxed values through NumPy ufuncs.

```python
import autograd.numpy as np
import xarray as xr
from autograd import grad

base = xr.DataArray(np.array([0.25, 1.0, -1.5]), dims=["feature"])


def loss(weights):
    out = np.sin(base * weights) + np.maximum(base * weights, 0.0)
    return np.sum(out.data)

weights = np.array([1.2, -0.7, 0.4])
print(grad(loss)(weights))
```

Notes:

- Keep the container during the ufunc step.
- Use `.data` or an equivalent extraction before the final scalar reduction.
- If xarray is missing, the wrapper layer still works; only this interop pattern is skipped.

## 3. SciPy wrapper smoke

Use this when you need to confirm that the installed environment exposes the selected SciPy wrappers.

```python
import autograd.numpy as np
from autograd.scipy import integrate, linalg, signal, special, stats

print(special.logsumexp(np.array([1.0, 2.0, 3.0])))
print(signal.convolve(np.array([1.0, 2.0, 3.0]), np.array([0.5, -1.0]), mode="full"))
print(linalg.solve_triangular(np.array([[2.0, 0.0], [1.0, 3.0]]), np.array([2.0, 5.0]), lower=True))
print(stats.norm.logpdf(0.5, loc=0.5, scale=2.0))
```

For `odeint`, keep the system tiny and synthetic:

```python
from autograd.scipy import integrate

def rhs(y, t, a):
    return -a * y

print(integrate.odeint(rhs, np.array([1.0]), np.linspace(0.0, 1.0, 4), args=(0.5,)))
```

## 4. Missing optional dependencies

If `autograd.scipy` or `xarray` is absent, use the bundled smoke helper to confirm the exact message and the suggested install step.

```bash
python scripts/wrappers_smoke.py --simulate-missing scipy
python scripts/wrappers_smoke.py --simulate-missing xarray
```

Use `--strict` when you want the run to fail instead of skipping optional sections.

## Boundary reminder

If the user needs a new derivative operator, a custom primitive, or a custom VJP/JVP rule, hand off to the sibling sub-skill instead of extending these workflows here.
