# Getting started with NumPyro

NumPyro is a probabilistic programming library that uses JAX for automatic differentiation, vectorization, JIT compilation, and CPU/GPU/TPU execution. Model code uses Pyro-like primitives (`sample`, `param`, `plate`) but follows JAX's functional and explicit-randomness style.

## Install choices

```bash
pip install numpyro
```

If JAX wheel compatibility is the issue, explicitly choose the CPU extra:

```bash
pip install 'numpyro[cpu]'
```

For NVIDIA GPU acceleration, install a CUDA-enabled JAX build matching the host driver and JAX's wheel guidance. NumPyro exposes CUDA extras such as:

```bash
pip install 'numpyro[cuda12]' -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
pip install 'numpyro[cuda13]' -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
```

For TPU, set up the TPU JAX runtime first, then install NumPyro. Do not treat the presence of hardware as proof of backend readiness; verify `jax.devices()` and a tiny device operation.

## Minimal import and backend smoke

```python
from jax import random
import jax
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist

print("numpyro", numpyro.__version__)
print("backend", jax.default_backend())
print("devices", jax.devices())
x = dist.Normal(0.0, 1.0).sample(random.key(0), sample_shape=(3,))
assert bool(jnp.isfinite(dist.Normal(0.0, 1.0).log_prob(x)).all())
```

Use [../scripts/check_numpyro_environment.py](../scripts/check_numpyro_environment.py) for a fuller diagnostic.

## Mental model for an end-to-end workflow

1. **Define a model** with explicit data arguments and NumPyro primitives. Use [../sub-skills/modeling-primitives/](../sub-skills/modeling-primitives/) for site, handler, trace, and plate semantics.
2. **Validate distributions** outside the model: constructor parameters, support, batch/event shapes, transforms, and finite `log_prob`. Use [../sub-skills/distributions-transforms/](../sub-skills/distributions-transforms/).
3. **Choose inference.** Use [../sub-skills/mcmc-diagnostics/](../sub-skills/mcmc-diagnostics/) for NUTS/HMC/MCMC and diagnostics; use [../sub-skills/svi-autoguides/](../sub-skills/svi-autoguides/) for SVI, guides, ELBOs, and optimization.
4. **Generate predictions or scores** with `Predictive` and `log_likelihood` after fitting.
5. **Escalate to contrib** only when the task needs optional features such as Funsor enumeration helpers, HSGP, nested sampling, TFP wrappers, Flax/Equinox modules, or SteinVI. Use [../sub-skills/advanced-contrib/](../sub-skills/advanced-contrib/).

## Tiny model example

```python
from jax import random
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS


def model(y=None):
    loc = numpyro.sample("loc", dist.Normal(0.0, 1.0))
    scale = numpyro.sample("scale", dist.HalfNormal(1.0))
    with numpyro.plate("data", 5 if y is None else y.shape[0]):
        numpyro.sample("obs", dist.Normal(loc, scale), obs=y)


y = jnp.array([0.8, 1.0, 1.1, 0.9, 1.2])
mcmc = MCMC(NUTS(model), num_warmup=100, num_samples=200, progress_bar=False)
mcmc.run(random.key(0), y)
samples = mcmc.get_samples()
assert samples["loc"].shape == (200,)
```

## Key differences from Pyro/PyTorch habits

- There is no global random state. Use JAX PRNG keys directly or through `handlers.seed`/inference algorithms.
- There is no global parameter store. `numpyro.param` values are managed by handlers or inference states such as SVI.
- Use `jax.numpy` and JAX-compatible control flow for values that may be traced.
- PyTorch neural modules must be rewritten or wrapped through optional JAX/Flax/Equinox paths.
- JIT compilation can make the first run slow; later same-shaped runs are often faster.

## What not to do

- Do not run large dataset examples or notebooks just to test installation. Use tiny synthetic scripts first.
- Do not install all optional dependency groups for ordinary core modeling/inference.
- Do not claim GPU/TPU verification unless the corresponding JAX backend is installed and a device smoke passes.
- Do not hide distribution support or model shape errors behind longer MCMC/SVI runs.
