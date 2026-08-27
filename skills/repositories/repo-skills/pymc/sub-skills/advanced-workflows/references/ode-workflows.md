# ODE workflows

`pm.ode.DifferentialEquation(func, times, *, n_states, n_theta, t0=0)` wraps an ODE system for PyMC likelihoods.

Rules:
- `func(y, t, p)` returns one derivative per state.
- `n_states` equals the length of `y0` and the number of state derivatives returned.
- `n_theta` equals the number of parameters passed in `theta`.
- Observed state output should align with `(len(times), n_states)`.
- Keep return values list/array-like, not dictionaries or nested unsupported structures.

Minimal pattern:

```python
def system(y, t, p):
    return [p[0] * y[0]]

ode = pm.ode.DifferentialEquation(func=system, times=times, n_states=1, n_theta=1)
with pm.Model() as model:
    alpha = pm.HalfNormal("alpha", 1)
    y_hat = ode(y0=[1.0], theta=[alpha])
    pm.Normal("obs", mu=y_hat, sigma=0.1, observed=observed)
```

Run a tiny `_simulate`/logp check before full sampling when shape errors appear.
