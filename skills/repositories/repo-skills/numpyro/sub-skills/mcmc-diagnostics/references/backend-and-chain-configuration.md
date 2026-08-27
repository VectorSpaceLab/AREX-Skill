# Backend and chain configuration

Configure JAX/NumPyro backend behavior before the first substantial JAX computation. Backend choices affect compilation, device placement, available parallel chains, dtype precision, and whether accelerator-specific code is actually verified.

## Minimal CPU setup

```python
import numpyro

numpyro.set_platform("cpu")          # optional when CPU is already the default
numpyro.set_host_device_count(4)     # only if you want 4 CPU devices/chains
```

Call these at the top of the program, before creating large arrays or importing modules that force JAX device initialization.

## Platform selection

| Goal | Setup | Caveat |
|---|---|---|
| Force CPU | `numpyro.set_platform("cpu")` or `JAX_PLATFORM_NAME=cpu` before running Python | Useful for reproducible CPU checks and avoiding accidental GPU memory use. |
| Use GPU | Install a CUDA-enabled JAX/JAXLIB build compatible with the driver, then `numpyro.set_platform("gpu")` if needed | A visible NVIDIA GPU is not enough; `jax.default_backend()` must report a GPU backend and tiny array ops must work. |
| Use TPU | Follow Cloud TPU JAX setup, then install NumPyro | TPU backend availability is environment-specific; verify with `jax.devices()`. |
| Enable x64 | `numpyro.enable_x64()` or `JAX_ENABLE_X64=1` | Must happen before arrays are created; improves numerical stability but can be slower. |

Backend smoke:

```python
import jax
import jax.numpy as jnp
print(jax.default_backend())
print(jax.devices())
_ = jnp.ones((1,)) + 1
```

Do not claim CUDA/TPU verification from a CPU-only smoke test. CPU can validate NumPyro model semantics, but accelerator wheel/driver/device behavior must be checked separately.

## `num_chains` and `chain_method`

`MCMC(..., num_chains=..., chain_method=...)` accepts:

| `chain_method` | Meaning | Use when |
|---|---|---|
| `"parallel"` | Run chains across XLA devices with `pmap`; falls back to sequential when too few devices are available. | Multiple CPU host devices, GPUs, or TPUs are available and progress bars are acceptable. |
| `"sequential"` | Run chains one after another. | Reproducible fallback when only one device is available or memory is tight. |
| `"vectorized"` | Vectorize chains on one device. | You want parallel chain-like behavior on one device; required for `AIES`/`ESS`. Experimental. |
| callable transform | Custom JAX transform such as `jax.vmap`/`jax.pmap`. | Expert workflows; progress bar is disabled when callable + multiple chains. |

If you request parallel chains on CPU and see a warning about not enough devices, call `numpyro.set_host_device_count(num_chains)` before JAX initializes:

```python
import numpyro
numpyro.set_host_device_count(4)
```

For command-line workflows, an equivalent is:

```bash
XLA_FLAGS=--xla_force_host_platform_device_count=4 python your_script.py
```

## Chain layout and output shape

- `mcmc.get_samples(group_by_chain=True)` returns a leading `(num_chains, num_samples, ...)` layout.
- `mcmc.get_samples()` flattens the first two dimensions to `(num_chains * num_samples, ...)`.
- Diagnostics should use grouped samples when possible; posterior predictive often uses flattened samples.
- `mcmc.get_extra_fields(group_by_chain=True)` mirrors the grouped sample layout for fields such as `num_steps` and `potential_energy`.

## Compilation and memory knobs

| Knob | Use | Caution |
|---|---|---|
| `jit_model_args=True` | Avoid recompiling potential energy for same-shaped but different-valued model arguments in repeated runs. | Does not help all multi-chain parallel cases. |
| `progress_bar=False` | Reduce overhead in tiny or many-chain runs. | Progress feedback is lost; can change memory behavior. |
| `mcmc.transfer_states_to_host()` | Move collected states from device to host memory after a run. | Use after sampling, before starting another large device computation. |
| `thinning` | Retain every `thinning`-th post-warmup sample. | Does not fix bad mixing; prefer better model/diagnostics first. |

## Optional GPU guidance

NumPyro uses JAX for device execution. GPU readiness requires all of:

1. Compatible hardware and driver.
2. CUDA-enabled JAX/JAXLIB installed for the correct CUDA generation.
3. `jax.default_backend()` or `jax.devices()` showing GPU devices.
4. A tiny device operation succeeding.
5. The target model running without device-specific dtype/memory errors.

If `jax` warns that a GPU is present but CUDA `jaxlib` is not installed, treat GPU as **unverified optional acceleration** and either install the documented CUDA extra or force CPU.

## x64 precision

Some distributions, MCMC geometries, nested sampling workflows, ODE/time-series examples, or covariance operations benefit from x64:

```python
import numpyro
numpyro.enable_x64()
```

Set it before creating arrays. If a result changes materially between float32 and x64, document the precision dependency in the analysis rather than hiding it as random MCMC noise.
