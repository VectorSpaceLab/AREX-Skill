# PyMC cross-cutting troubleshooting

Read this for install/import and package-wide runtime failures. Workflow-specific failures live in the nearest sub-skill troubleshooting reference.

## Import or install fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pymc'` | Package not installed in the active Python. | Install `pymc` into the Python that will run the code. Run `python scripts/check_pymc_env.py`. |
| `ModuleNotFoundError: No module named 'pytensor'` | Broken or incomplete PyMC dependency install. | Reinstall PyMC in a fresh environment; run `python -m pip check`. |
| Resolver wants incompatible Python or compiled wheels | Python version/environment conflict. | Use a fresh Python 3.12+ environment and avoid broad dev/docs extras unless needed. |
| `pip check` reports conflicts | Mixed packages from old scientific stack. | Prefer a fresh environment; pin only the optional packages actually needed. |

## PyTensor compiler and backend issues

- C compiler errors or long compilation usually point to PyTensor/system compiler setup, not necessarily model logic. Use a fresh Conda environment or a simpler compile backend for debugging when acceptable.
- Numba object-mode warnings can appear for ODE/custom operations. Accept for tiny smokes if results are finite; simplify operations or change backend when performance matters.
- BLAS/OpenMP oversubscription can make chains slow. Set `chains`, `cores`, and `blas_cores` deliberately.

## Optional sampler/backend failures

- `nutpie not found` or version warnings: install `pymc[nutpie]`/`nutpie>=0.16.10`, or pin `nuts_sampler="pymc"`.
- JAX reports GPU present but CUDA-enabled `jaxlib` missing: accept CPU JAX for CPU workflows; install a compatible CUDA JAX stack only for explicit GPU JAX tasks.
- External NUTS rejects `callback`, custom `trace`, or `return_inferencedata=False`: use `nuts_sampler="pymc"` for those features or remove incompatible options.

## ArviZ/DataTree output surprises

Current PyMC returns xarray `DataTree`-style groups. Access common groups as attributes (`idata.posterior`, `idata.sample_stats`, `idata.posterior_predictive`, `idata.predictions`, `idata.log_likelihood`) when present. If `log_likelihood` is missing, compute it explicitly with `pm.compute_log_likelihood(idata, model=model)` for observed models.

## Where to go next

- Shape, coordinates, `pm.Data`, `set_data`, `do`, or `observe`: `../sub-skills/modeling-data/references/troubleshooting.md`.
- Distribution support, `.dist()`, custom logp/logcdf, transforms, or broadcasting: `../sub-skills/distributions-logprob/references/troubleshooting.md`.
- MCMC, predictive sampling, diagnostics, external samplers, Zarr/mcbackend: `../sub-skills/inference-predictive/references/troubleshooting.md`.
- Gaussian processes, ODE, VI, minibatches: `../sub-skills/advanced-workflows/references/troubleshooting.md`.
