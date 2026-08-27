# Cross-cutting NumPyro troubleshooting

## Install/import failures

**Symptoms**

- `ModuleNotFoundError: No module named 'numpyro'`
- `ImportError` from `jax`, `jaxlib`, or compiled dependencies
- Package imports from an unexpected checkout instead of the installed environment

**Fix**

1. Verify the active Python environment: `python -c "import sys; print(sys.executable); print(sys.version)"`.
2. Install the package or an appropriate extra: `pip install numpyro` or `pip install 'numpyro[cpu]'`.
3. Run `python -m pip check`.
4. Run `python scripts/check_numpyro_environment.py --pretty` from this skill.
5. If an editable checkout shadows the installed package, rerun checks from a neutral directory and inspect `numpyro.__file__` only for private debugging, not in published results.

## JAX backend confusion

**Symptoms**

- GPU is visible to system tools but JAX reports CPU.
- Warning says an NVIDIA GPU may be present but CUDA-enabled `jaxlib` is not installed.
- `jax.devices()` has fewer devices than `num_chains`.

**Fix**

- Force CPU for CPU-only work: `numpyro.set_platform("cpu")` before JAX initializes.
- For CPU parallel chains, call `numpyro.set_host_device_count(n)` before JAX initializes or run with `XLA_FLAGS=--xla_force_host_platform_device_count=n`.
- For CUDA, install a CUDA-enabled JAX/JAXLIB build matching the driver and verify `jax.default_backend()` plus a tiny device operation.
- Do not call a CPU smoke test GPU verification.

## Optional dependency failures

**Symptoms**

- Missing `funsor`, `optax`, `flax`, `equinox`, `tensorflow_probability`, `jaxns`, `graphviz`, `matplotlib`, `pandas`, or `sklearn`.
- A contrib import fails but core `numpyro` imports work.

**Fix**

- Route to [../sub-skills/advanced-contrib/](../sub-skills/advanced-contrib/) and run `check_optional_dependencies.py`.
- Install only the dependency required by the selected workflow.
- Keep core modeling/MCMC/SVI tasks on base NumPyro when contrib features are not needed.

## Data downloads and examples

Many public NumPyro examples use dataset loaders that download external data into a cache. Do not use those examples as installation smokes unless the task explicitly allows network/data acquisition.

Safer order:

1. Run bundled synthetic scripts in this skill.
2. Run repo-native examples only after their dependencies and data side effects are understood.
3. Prefer example options that use synthetic/mock data when available.

## Numerical precision and dtype

**Symptoms**

- Non-finite log probabilities for covariance/heavy-tail/time-series/ODE models.
- Results differ substantially between runs with stable seeds.
- Tests or examples mention x64.

**Fix**

Call `numpyro.enable_x64()` or set `JAX_ENABLE_X64=1` before arrays and JAX computations are created. Re-run a tiny support/log-prob check and then rerun inference.

## JAX tracer and side-effect errors

**Symptoms**

- `TracerBoolConversionError`, `ConcretizationTypeError`, or failures only under JIT/vectorization/MCMC/SVI.
- Python list mutation or value-dependent branching inside model execution.

**Fix**

- Use `jax.numpy` operations for traced values.
- Replace value-dependent loops/branches with JAX or NumPyro control flow.
- Keep plotting, file I/O, downloads, logging side effects, and non-JAX randomness outside model and guide execution.

## Slow first run

JAX compilation can dominate the first model/inference call. Distinguish compilation from algorithmic slowness:

- Validate with tiny synthetic data and small warmup/step counts.
- Repeat a same-shaped run to see whether compilation is amortized.
- Use `jit_model_args=True` for repeated MCMC runs with same-shaped data when appropriate.
- Disable progress bars for tiny or heavily vectorized runs.

## Inference failure routing

| Symptom | First route |
|---|---|
| Distribution `log_prob` non-finite or support invalid | [distributions-transforms](../sub-skills/distributions-transforms/) |
| Plate, trace, conditioning, or handler metadata wrong | [modeling-primitives](../sub-skills/modeling-primitives/) |
| MCMC divergences, `r_hat`, ESS, chain/device warnings | [mcmc-diagnostics](../sub-skills/mcmc-diagnostics/) |
| SVI NaN losses, guide parameter constraints, wrong ELBO | [svi-autoguides](../sub-skills/svi-autoguides/) |
| Missing optional contrib dependency | [advanced-contrib](../sub-skills/advanced-contrib/) |
