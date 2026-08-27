# Inference API reference

## `pm.sample`

Key arguments: `draws`, `tune`, `chains`, `cores`, `random_seed`, `progressbar`, `quiet`, `step`, `var_names`, `nuts_sampler`, `initvals`, `init`, `trace`, `discard_tuned_samples`, `compute_convergence_checks`, `return_inferencedata`, `idata_kwargs`, `callback`, `blas_cores`, `backend`, `compile_kwargs`, and step kwargs such as `nuts={"target_accept": 0.9}`.

`nuts_sampler` is one of `"pymc"`, `"nutpie"`, `"numpyro"`, `"blackjax"`, or `None` for auto. `nuts_sampler_kwargs` exists but is deprecated in favor of `nuts={...}`.

External samplers cannot use custom traces, callbacks, or `return_inferencedata=False`. `nutpie` requires `nutpie>=0.16.10`. JAX samplers require JAX plus `numpyro` or `blackjax`.

## Forward sampling

```python
pm.sample_prior_predictive(draws=500, model=None, var_names=None, random_seed=None, return_inferencedata=True)
pm.sample_posterior_predictive(trace, model=None, var_names=None, sample_vars=None, freeze_vars=None, sample_dims=None, random_seed=None, predictions=False, extend_inferencedata=False, return_inferencedata=True)
pm.draw(vars, draws=1, random_seed=None, backend=None, **kwargs)
```

Use `var_names` for output selection. Use `sample_vars` to force regeneration of trace variables and `freeze_vars` to force reuse/silence implicit-freeze warnings.

## SMC and log likelihood

`pm.sample_smc(draws=2000, kernel=..., chains=None, cores=None, random_seed=None, return_inferencedata=True, ...)` is a specialized alternative for some multimodal or discrete-heavy problems. `pm.compute_log_likelihood(idata, var_names=None, extend_inferencedata=True, model=None, sample_dims=("chain", "draw"))` adds or returns a `log_likelihood` group for model comparison.
