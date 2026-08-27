# NumPyro advanced contrib overview

This reference distills the operating rules for optional and experimental NumPyro contrib areas. Use it to decide whether a request belongs in `advanced-contrib`, which dependency probe to run, and where to reroute core work.

## Capability map

| Area | Use when the user needs | Primary APIs | Dependency caveat | Reroute when |
| --- | --- | --- | --- | --- |
| Funsor enumeration | Exact marginalization or posterior decoding for discrete latent variables; HMM-like Markov structure; enumerated SVI | `config_enumerate`, `infer_discrete`, `markov`, `enum`, `log_density` | Requires `funsor`; shape semantics differ from ordinary sampled tensors | The task is ordinary discrete sampling, `DiscreteHMCGibbs`, or core plate/indexing work |
| HSGP | Fast low-rank GP terms inside NumPyro models | `hsgp_squared_exponential`, `hsgp_matern`, `hsgp_rational_quadratic`, `hsgp_periodic_non_centered`, `eigenfunctions`, spectral-density helpers | Base import is light, but periodic/RQ spectral densities require TFP at call time | The user wants an exact GP, distribution semantics, or MCMC diagnostics |
| Nested sampling | Evidence-oriented or multimodal posterior exploration, including some discrete/non-invertible models | `NestedSampler`, `get_samples`, `get_weighted_samples`, `print_summary`, `diagnostics` | Requires `jaxns` and the TFP JAX substrate; x64 is strongly recommended | The request is ordinary NUTS/HMC/MCMC tuning |
| Einstein SteinVI | Particle-based VI that can represent correlations or multimodality better than a single mean-field guide | `SteinVI`, `SVGD`, `ASVGD`, `RBFKernel`, `MixtureGuidePredictive` | Core SteinVI imports without the common example-only dependencies, but real examples often add plotting/data/Optax dependencies | The task is standard SVI, autoguide choice, or ELBO debugging |
| Neural module wrappers | Register neural-network parameters or priors inside NumPyro models | `flax_module`, `random_flax_module`, `nnx_module`, `random_nnx_module`, `eqx_module`, `random_eqx_module` | Flax, Flax NNX, and Equinox are optional and fail independently | The task is plain `numpyro.module` or primitive `param` handling |
| TFP integration | Use TFP JAX distributions or TFP MCMC transition kernels from NumPyro | Direct `tensorflow_probability.substrates.jax.distributions`; `TFPDistribution`; `numpyro.contrib.tfp.mcmc` | Requires a TFP build compatible with installed JAX; contrib wrapper distributions warn that direct TFP imports are preferred | A native NumPyro distribution/kernel exists and is sufficient |
| Stochastic support | Models whose execution path/support changes after discrete stochastic branches | `DCC`, `SDVI`, `StochasticSupportInference`, `infer={"branching": True}` | Branching sites must be discrete; local inference can be expensive per straight-line program | The model has fixed support and can use ordinary SVI/MCMC |

## Funsor enumeration operating notes

Use Funsor when discrete latent variables should be marginalized rather than sampled directly. Typical patterns:

```python
from numpyro.contrib.funsor import config_enumerate, infer_discrete, markov
from numpyro.infer import SVI, TraceEnum_ELBO

@config_enumerate
def model(data):
    ...
    z = numpyro.sample("z", dist.Categorical(probs), infer={"enumerate": "parallel"})
    ...

svi = SVI(model, guide, optimizer, loss=TraceEnum_ELBO())
posterior_model = infer_discrete(model, first_available_dim=-1, temperature=1, rng_key=rng_key)
```

Key decisions:

- Use `config_enumerate` to set a default enumeration policy; still annotate the discrete sample sites whose enumeration must be explicit.
- Use `infer_discrete(..., temperature=0)` for most-probable discrete assignments and `temperature=1` for posterior sampling. Provide `rng_key` when sampling.
- Use `markov` for sequential dependence in HMM-like loops. For scanned Markov models, be conservative with enum dimensions and test a short sequence first.
- When indexing by an enumerated value, prefer `Vindex`-style advanced indexing instead of ordinary positional indexing that may broadcast incorrectly.
- Funsor absence usually appears as `ModuleNotFoundError: No module named 'funsor'`; verify with `--require funsor`.

## HSGP operating notes

Use HSGP for approximate GP latent functions where exact covariance inversion would be too expensive. Build it as a model component, not as a standalone inference algorithm:

```python
from numpyro.contrib.hsgp.approximation import hsgp_squared_exponential

f = hsgp_squared_exponential(
    x=x_scaled,
    alpha=alpha,
    length=length,
    ell=1.3,
    m=20,
    non_centered=True,
)
```

Important choices:

- Scale inputs so the modeled domain is comfortably inside `[-ell, ell]` per dimension. Boundary points degrade approximation quality.
- `m` controls the basis count. In multiple dimensions the basis size is the product of per-dimension counts, so avoid blindly increasing all entries.
- `hsgp_squared_exponential` and `hsgp_matern` are the lowest-dependency choices.
- `hsgp_rational_quadratic` requires a scalar/isotropic length in multi-dimensional settings and needs TFP for Bessel functions.
- `hsgp_periodic_non_centered` is univariate only and needs TFP for Bessel functions.

See [HSGP, TFP, and nested sampling](hsgp-and-tfp.md) for details.

## Nested sampling operating notes

Use `NestedSampler` when the user asks for nested sampling, model evidence, multimodal shell-like posteriors, or a non-MCMC alternative that can handle awkward latent geometry. Basic pattern:

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
samples = ns.get_samples(random.key(1), num_samples=500)
```

Caveats:

- Importing `NestedSampler` requires `jaxns` and TFP. Missing `jaxns` is the common first failure; missing TFP can appear after `jaxns` is installed.
- Enable x64 for serious nested sampling runs.
- Discrete latent variables can be marked with `infer={"enumerate": "parallel"}`.
- `diagnostics()` creates plots; do not call it in headless or no-plotting contexts unless plotting dependencies and an output policy are explicit.
- Some priors require inverse-CDF support for the uniform reparameterization; unsupported inverse CDF paths can fail even if imports succeed.

## Einstein SteinVI operating notes

Use `numpyro.contrib.einstein` when the user wants particle-based variational inference or Stein variational gradient descent:

```python
from numpyro.contrib.einstein import MixtureGuidePredictive, RBFKernel, SteinVI
from numpyro.infer.autoguide import AutoNormal
from numpyro.optim import Adam

guide = AutoNormal(model)
stein = SteinVI(model, guide, Adam(0.01), RBFKernel(), num_stein_particles=8)
result = stein.run(rng_key, 200, *args, progress_bar=False)
predictive = MixtureGuidePredictive(
    model,
    guide=stein.guide,
    params=stein.get_params(result.state),
    guide_sites=stein.guide_sites,
    num_samples=100,
)
```

Choose among:

- `SteinVI`: Stein mixture inference with a user-supplied guide.
- `SVGD`: direct Stein variational gradient descent wrapper.
- `ASVGD`: annealed SVGD schedule.
- Kernels: `RBFKernel` is the practical default; other kernels include `LinearKernel`, `RandomFeatureKernel`, `MixtureKernel`, `GraphicalKernel`, `ProbabilityProductKernel`, and `RadialGaussNewtonKernel`.

Keep Stein examples bounded. Large BNN/DMM examples often include datasets, plotting, scikit-learn, Optax, or music/visualization dependencies that are not needed for a tiny smoke test of the API.

## Neural module wrappers

Use `numpyro.contrib.module` when integrating a Flax Linen, Flax NNX, or Equinox module with NumPyro parameter or prior semantics.

### Deterministic parameter wrappers

- `flax_module("name", linen_module, input_shape=...)` initializes a Flax Linen module and registers `name + "$params"` via `numpyro.param`.
- `nnx_module("name", nnx_module_instance)` expects an eagerly initialized Flax NNX module instance outside the probabilistic model.
- `eqx_module("name", eqx_module_instance)` expects an eagerly initialized Equinox module; use `jax.vmap` yourself for batched Equinox calls.

### Random/prior wrappers

- `random_flax_module`, `random_nnx_module`, and `random_eqx_module` sample selected parameter leaves from NumPyro distributions.
- `prior` may be a distribution, a dictionary keyed by parameter-path strings, or a callable `(name, shape) -> distribution`.
- Random wrappers put sample sites under a scoped name such as `net/kernel`, `net/bias`, or a custom divider.
- Flax Linen supports `input_shape`, positional initialization arguments, keyword initialization arguments, `apply_rng` for stochastic layers, and `mutable` for state such as batch statistics.
- NNX and Equinox stateful computations use NumPyro mutable state holders; test tiny traces before running inference.

Difficult case: if a user asks for `flax_module` or `random_flax_module` and sees `ModuleNotFoundError: No module named 'flax'`, do not rewrite the model as core NumPyro. Explain that Flax is an optional dependency, install/verify it, and preserve the parameter handling described above.

## TFP integration notes

Use TFP only when the needed distribution or transition kernel is absent from native NumPyro or the user explicitly requests TFP.

- Prefer direct JAX substrate distributions in model code:
  ```python
  from tensorflow_probability.substrates.jax import distributions as tfd
  numpyro.sample("x", tfd.Normal(0.0, 1.0))
  ```
- `numpyro.contrib.tfp.distributions.TFPDistribution[tfd.SomeDistribution]` exists for compatibility, but the wrapper warns that direct TFP distribution imports are preferred.
- TFP MCMC wrappers expose TFP transition kernels as NumPyro `MCMCKernel` classes. Construct them with exactly one of `model=` or `potential_fn=`; if using `potential_fn`, pass `init_params` to `MCMC.run`.
- Uncalibrated TFP kernels are wrapped in a Metropolis-Hastings correction internally.

## Stochastic support operating notes

Use stochastic-support inference when discrete stochastic branches change which later sample sites exist or which support applies.

```python
from numpyro.contrib.stochastic_support.dcc import DCC
from numpyro.contrib.stochastic_support.sdvi import SDVI

branch = numpyro.sample("branch", dist.Bernoulli(0.5), infer={"branching": True})
```

- Branching sites must be discrete. Continuous branch sites raise a runtime error.
- `DCC` discovers straight-line programs, runs local MCMC on each one, then combines samples with SLP weights.
- `SDVI` discovers straight-line programs, trains a guide per SLP, then weights guides by ELBO estimates.
- Bound `num_slp_samples`, `max_slps`, MCMC samples, and SVI steps for exploratory work; the cost scales with discovered branches.

## Safe bounded workflow

1. Classify the request and reroute core-only work to the sibling sub-skills.
2. Run `python scripts/check_optional_dependencies.py --pretty` from this sub-skill directory, or require only the needed capability.
3. If imports are missing, explain the optional dependency rather than changing the model silently.
4. Use a tiny synthetic smoke case before running any large example, dataset loader, nested sampler, or Stein training loop.
5. Avoid benchmark guidance and maintainer-only scripts; contrib examples can be long-running and may create plots or download data.
