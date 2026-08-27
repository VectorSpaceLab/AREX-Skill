# HSGP, TFP, and nested sampling guidance

This reference covers three contrib areas with subtle optional dependencies: Hilbert-space Gaussian process approximations, TensorFlow Probability integration, and `jaxns` nested sampling.

## HSGP approximations

HSGP functions are model components that create latent functions through low-rank Laplacian bases and spectral densities. They are useful when a full GP covariance matrix would be too expensive.

### Main approximation functions

| Function | Kernel | Extra dependency at call time | Key caveats |
| --- | --- | --- | --- |
| `hsgp_squared_exponential(x, alpha, length, ell, m, non_centered=True)` | Squared exponential | None beyond core imports | Scale `x`; choose `ell` so data stay away from boundaries; `m` controls basis count |
| `hsgp_matern(x, nu, alpha, length, ell, m, non_centered=True)` | Matérn | None beyond core imports | Same domain/basis caveats; choose `nu` consciously |
| `hsgp_rational_quadratic(x, alpha, length, scale_mixture, ell, m, non_centered=True)` | Rational quadratic | TFP JAX substrate for Bessel functions | Isotropic/scalar length in multi-dimensional settings; `scale_mixture > dim / 2` for finite zero-frequency density |
| `hsgp_periodic_non_centered(x, alpha, length, w0, m)` | Periodic squared exponential | TFP JAX substrate for Bessel functions | Univariate inputs only; use `w0 = 2 * pi / period` if parameterizing by period |

### Basis and spectral-density helpers

- `eigenindices(m, dim)`: builds the index grid for the first basis functions.
- `sqrt_eigenvalues(ell, m, dim)`: square roots of Laplacian eigenvalues on the approximation box.
- `eigenfunctions(x, ell, m)`: basis evaluated at `x`; if `x` is one-dimensional, the model is treated as 1D.
- `eigenfunctions_periodic(x, w0, m)`: periodic basis; rejects multidimensional inputs.
- Spectral densities include squared-exponential, Matérn, rational-quadratic, and periodic diagonal helpers.

### Safe HSGP modeling pattern

```python
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.contrib.hsgp.approximation import hsgp_squared_exponential


def model(x, y=None):
    alpha = numpyro.sample("alpha", dist.HalfNormal(1.0))
    length = numpyro.sample("length", dist.InverseGamma(6.0, 1.0))
    noise = numpyro.sample("noise", dist.HalfNormal(0.5))
    f = hsgp_squared_exponential(
        x=x,
        alpha=alpha,
        length=length,
        ell=1.3,
        m=20,
        non_centered=True,
    )
    with numpyro.plate("data", x.shape[0]):
        numpyro.sample("obs", dist.Normal(f, noise), obs=y)
```

Operational checks:

1. Center/scale `x` first; choose `ell` larger than the maximum absolute scaled input.
2. In `D` dimensions, set `x.shape[-1] == D` and keep `m` modest because basis count is `prod(m)`.
3. Prefer non-centered parameterization initially.
4. For periodic/RQ kernels, verify `python scripts/check_optional_dependencies.py --require hsgp_tfp`.
5. Do not treat approximation error as an MCMC bug until `ell`, `m`, scaling, and kernel assumptions have been checked.

## TensorFlow Probability distributions

Use TFP when a distribution is unavailable in native NumPyro or the user explicitly requests it.

Preferred direct pattern:

```python
from tensorflow_probability.substrates.jax import distributions as tfd


def model():
    x = numpyro.sample("x", tfd.Normal(0.0, 1.0))
    numpyro.sample("obs", tfd.Bernoulli(logits=x), obs=1)
```

Compatibility wrapper pattern:

```python
from tensorflow_probability.substrates.jax import distributions as tfd
from numpyro.contrib.tfp.distributions import TFPDistribution

d = TFPDistribution[tfd.Normal](0.0, 1.0)
```

The wrapper exists, but direct TFP JAX substrate distributions are preferred. The wrapper forwards sampling/log-probability and maps many TFP constraints/bijectors into NumPyro-compatible transforms.

Caveats:

- TFP/JAX compatibility is version-sensitive. If imports fail with substrate or tracer errors, verify TFP against the installed JAX version.
- Native NumPyro distributions are usually simpler for common distributions.
- Some TFP distribution tests or MCMC wrappers may be skipped upstream because of pending TFP releases; use a tiny smoke test before relying on a specific kernel or distribution family.

## TFP MCMC wrappers

`numpyro.contrib.tfp.mcmc` turns TFP transition kernels into NumPyro `MCMCKernel` classes.

```python
from numpyro.contrib.tfp import mcmc as tfp_mcmc
from numpyro.infer import MCMC

kernel = tfp_mcmc.NoUTurnSampler(model=model, step_size=0.05)
mcmc = MCMC(kernel, num_warmup=100, num_samples=100, progress_bar=False)
mcmc.run(rng_key, *model_args)
```

Rules:

- Construct with exactly one of `model=` or `potential_fn=`.
- If using `potential_fn=`, pass compatible `init_params` to `MCMC.run`.
- The wrapped TFP kernel must accept `target_log_prob_fn` as its first constructor argument.
- Uncalibrated TFP kernels are internally wrapped with Metropolis-Hastings.
- `ReplicaExchangeMC` has special `step_size` shape requirements tied to inverse temperatures.

## Nested sampling through jaxns

`NestedSampler` wraps `jaxns` for NumPyro models.

```python
from jax import random
import numpyro
from numpyro.contrib.nested_sampling import NestedSampler

numpyro.enable_x64()
ns = NestedSampler(
    model,
    constructor_kwargs={"num_live_points": 100, "max_samples": 2000},
    termination_kwargs={"dlogZ": 1e-3},
)
ns.run(random.key(0), *model_args, **model_kwargs)
weighted_samples, log_weights = ns.get_weighted_samples()
samples = ns.get_samples(random.key(1), num_samples=500)
```

Use it when:

- The user explicitly asks for nested sampling or `jaxns`.
- The posterior is multimodal or has non-invertible geometry where a non-MCMC approach is desired.
- Model evidence/log-normalization is important.

Avoid it when:

- The environment lacks `jaxns` or TFP and installation is not allowed.
- The task is ordinary NUTS/HMC diagnostics.
- The model uses priors whose inverse-CDF reparameterization is unsupported.
- The run budget cannot tolerate many live points or a long termination schedule.

Important caveats:

- Importing `NestedSampler` can fail on `jaxns` first and TFP second; require `nested_sampling` with the checker.
- Enable x64 before serious nested sampling; tests for this area expect double precision.
- Discrete latent variables can be enumerated by marking sites with `infer={"enumerate": "parallel"}`.
- `print_summary()` writes text; `diagnostics()` plots. Treat plotting as a side effect requiring explicit user intent.
- Default constructor values include live points based on latent dimensionality, all visible JAX devices, and a maximum sample bound. Override these for bounded CPU smoke tests.

## Difficult nested-sampling failure case

Symptom: a user asks for nested sampling and `from numpyro.contrib.nested_sampling import NestedSampler` fails with a message that `jaxns` is missing.

Response pattern:

1. Say this is an optional dependency gap, not a core NumPyro failure.
2. Verify with `python scripts/check_optional_dependencies.py --require nested_sampling --pretty`.
3. Install/verify `jaxns` and a compatible TFP JAX substrate if environment policy allows installation.
4. Re-run a tiny bounded `NestedSampler` smoke case with `num_live_points` and `max_samples` explicitly limited.
5. If installation is impossible, reroute to core MCMC and explain that evidence-style nested sampling is unavailable.
