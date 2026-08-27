# Distribution workflows

## Use `.dist()` for components

```python
with pm.Model() as model:
    mu_left = pm.Normal("mu_left", -1, 1)
    mu_right = pm.Normal("mu_right", 1, 1)
    weights = pm.Dirichlet("weights", a=[1, 1])
    components = [pm.Normal.dist(mu_left, 1), pm.Normal.dist(mu_right, 1)]
    y = pm.Mixture("y", w=weights, comp_dists=components, observed=data)
```

The parent parameters are named and sampled; the component distributions are unregistered tensors. Passing already-registered component RVs is a common error.

## Validate logp and shape before sampling

```python
rv = pm.Normal.dist(0, 1, shape=(3,))
logp = pm.logp(rv, [0.0, 0.1, -0.1]).eval()
assert logp.shape == (3,)
```

For a model, use `model.initial_point()` and `model.compile_logp()`. For distribution-only debugging, `pm.logp` and `pm.draw` are usually quicker.

## Custom distribution pattern

```python
def random(mu, rng=None, size=None):
    return rng.normal(mu, 1, size=size)

def logp(value, mu):
    return pm.logp(pm.Normal.dist(mu, 1), value)

def support_point(rv, size, mu):
    return pm.math.full(size, mu, dtype=rv.dtype)

with pm.Model() as model:
    mu = pm.Normal("mu")
    obs = pm.CustomDist("obs", mu, random=random, logp=logp, support_point=support_point, observed=data)
```

Posterior predictive sampling needs `random`. If only `logp` is supplied, inference may work but forward/predictive draws will fail.

## Family routing

- Positive continuous support: Gamma, Exponential, HalfNormal, LogNormal, Weibull, InverseGamma, PolyaGamma when installed.
- Unit interval/simplex support: Beta, Dirichlet, Logistic transforms.
- Counts/categories: Poisson, NegativeBinomial, Binomial, Categorical, Multinomial.
- Mixtures/zero-inflation/hurdles: `Mixture`, `NormalMixture`, zero-inflated and hurdle classes.
- Truncation/censoring: use wrappers around base `.dist()` distributions.
- Time series/simulator/custom likelihoods: use the specific family when available before writing unstructured `Potential`s.
