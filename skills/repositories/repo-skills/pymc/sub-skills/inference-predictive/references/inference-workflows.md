# Inference and predictive workflows

## Tiny safe smoke

```python
with model:
    idata = pm.sample(draws=10, tune=10, chains=1, cores=1, random_seed=123, progressbar=False, compute_convergence_checks=False, nuts_sampler="pymc")
```

This checks API wiring only. For real inference, use larger draws/tune/chains and inspect diagnostics.

## Choose a sampler

- Default PyMC NUTS: most compatible, supports callbacks/custom traces and mixed step method workflows.
- Nutpie: optional fast Rust NUTS for differentiable continuous models; may be auto-selected when installed and compatible.
- NumPyro/BlackJAX: optional JAX NUTS; useful when the model is JAX-compatible and optional dependencies are installed.
- Explicit step methods: combine `pm.NUTS`, `pm.Metropolis`, `pm.CategoricalGibbsMetropolis`, etc., when auto-assignment is not enough.

## Prior and posterior predictive

```python
prior = pm.sample_prior_predictive(draws=100, random_seed=1)
pp = pm.sample_posterior_predictive(idata, var_names=["y"], random_seed=2)
```

For out-of-sample predictions after changing `pm.Data`, update data and coords first, then use:

```python
pred = pm.sample_posterior_predictive(idata, var_names=["y"], predictions=True, random_seed=3)
```

`predictions=True` stores draws in the `predictions` group rather than ordinary in-sample `posterior_predictive`.

## Diagnostics

Check divergences, tree depth warnings, ESS, R-hat, posterior sizes, and whether log-likelihood is present before model comparison. If diagnostics fail, revisit model parameterization, priors, target acceptance, scaling, and data shape.
