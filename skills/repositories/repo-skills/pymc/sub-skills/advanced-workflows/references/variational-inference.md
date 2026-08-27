# Variational inference and minibatches

Use `pm.fit(n=..., method="advi")` or object APIs such as `pm.ADVI()` and `pm.FullRankADVI()` for fast approximate posterior fitting. Use `pm.sample_approx` or `approx.sample(draws=...)` to draw from the approximation.

```python
with model:
    approx = pm.fit(n=10000, method="advi", obj_optimizer=pm.adam(learning_rate=0.01))
    idata = approx.sample(draws=1000)
```

Use VI for initialization, exploratory checks, or large-data/minibatch workflows; do not present it as automatically more accurate than MCMC.

`pm.Minibatch(data, batch_size=...)` draws random leading-dimension slices. In likelihoods, pass `total_size` so logp scaling reflects the full dataset. Minibatch variables must be non-random observed/data variables and multiple minibatch arrays must have equal leading dimension.

Callbacks such as convergence trackers can stop or monitor VI. If loss becomes NaN or inf, lower learning rate, check initial logp, rescale data, and inspect priors/support.
