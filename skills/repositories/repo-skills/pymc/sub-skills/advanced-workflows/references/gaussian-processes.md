# Gaussian process workflows

Use `pm.gp.Marginal` for noisy observed GP regression with `(X, y)` and a Gaussian noise term. Use `pm.gp.Latent` when the latent function itself is a prior variable in the model. Use sparse/marginal approximations or HSGP for larger input grids or approximate workflows.

Typical noisy regression structure:

```python
with pm.Model() as model:
    ls = pm.Gamma("ls", alpha=2, beta=1)
    eta = pm.HalfNormal("eta", 1)
    cov = eta**2 * pm.gp.cov.ExpQuad(input_dim=1, ls=ls)
    gp = pm.gp.Marginal(cov_func=cov)
    sigma = pm.HalfNormal("sigma", 1)
    y = gp.marginal_likelihood("y", X=X, y=y_obs, sigma=sigma)
    f_new = gp.conditional("f_new", Xnew=Xnew)
```

Check `X` and `Xnew` are two-dimensional arrays `(n, input_dim)`. For prediction draws and output groups, route to `inference-predictive` after the conditional is part of the model.
