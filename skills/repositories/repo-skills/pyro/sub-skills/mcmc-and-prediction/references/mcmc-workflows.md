# MCMC Workflows

This reference covers Pyro 1.9.1-family MCMC usage for continuous latent-variable
models and models where discrete variables have been deliberately marginalized or
enumerated. It assumes the model's primitive, distribution, and plate contracts
are already valid; route those issues to sibling sub-skills first.

## Core API Facts

| Object | Runtime signature pattern | Use |
|---|---|---|
| `MCMC(kernel, num_samples, warmup_steps=None, initial_params=None, num_chains=1, hook_fn=None, mp_context=None, disable_progbar=False, disable_validation=True, transforms=None, save_params=None)` | Wraps a kernel and stores posterior draws. If `warmup_steps` is omitted it defaults to `num_samples`. | Run sampling with `mcmc.run(*model_args, **model_kwargs)`, then call `get_samples()`, `summary()`, or `diagnostics()`. |
| `NUTS(model=None, potential_fn=None, step_size=1, adapt_step_size=True, adapt_mass_matrix=True, full_mass=False, use_multinomial_sampling=True, transforms=None, max_plate_nesting=None, jit_compile=False, jit_options=None, ignore_jit_warnings=False, target_accept_prob=0.8, max_tree_depth=10, init_strategy=init_to_uniform)` | No-U-Turn Sampler; exactly one of `model` or `potential_fn` must be provided. | Preferred default HMC kernel when the model is differentiable and geometry is not already tuned. |
| `HMC(model=None, potential_fn=None, step_size=1, trajectory_length=None, num_steps=None, adapt_step_size=True, adapt_mass_matrix=True, full_mass=False, transforms=None, max_plate_nesting=None, jit_compile=False, jit_options=None, ignore_jit_warnings=False, target_accept_prob=0.8, init_strategy=init_to_uniform, min_stepsize=1e-10, max_stepsize=1e10)` | Fixed-trajectory HMC; exactly one of `model` or `potential_fn` must be provided. | Use when you intentionally control `num_steps` or `trajectory_length`, or when comparing to a known HMC configuration. |
| `mcmc.run(*args, **kwargs)` | Args/kwargs are passed to the kernel's model setup. | Populates retained samples; returns `None`. |
| `mcmc.get_samples(num_samples=None, group_by_chain=False)` | With `num_samples=None`, returns all retained samples. With an integer, resamples with replacement. | Use `group_by_chain=True` when computing or inspecting chain-specific shapes. |
| `mcmc.summary(prob=0.9)` | Prints mean, std, median, credible interval, effective sample size, split R-hat, and divergence count when available. | Human-readable convergence summary; not a formal proof of convergence. |
| `mcmc.diagnostics()` | Returns an ordered dict per saved site plus kernel diagnostics such as divergences and acceptance rate. | Programmatic checks for `n_eff`, `r_hat`, divergent transitions, and per-chain kernel info. |

Import pattern:

```python
import pyro
import pyro.distributions as dist
from pyro.infer import MCMC, NUTS, HMC, Predictive
```

## Minimal NUTS Recipe

```python
import torch
import pyro
import pyro.distributions as dist
from pyro.infer import MCMC, NUTS


def model(data):
    loc = pyro.sample("loc", dist.Normal(data.new_tensor(0.0), 5.0))
    scale = pyro.sample("scale", dist.LogNormal(data.new_tensor(0.0), 0.5))
    with pyro.plate("data", data.size(0), dim=-1):
        pyro.sample("obs", dist.Normal(loc, scale), obs=data)

pyro.set_rng_seed(0)
pyro.clear_param_store()
pyro.enable_validation(True)

kernel = NUTS(
    model,
    target_accept_prob=0.8,
    max_tree_depth=10,
)
mcmc = MCMC(
    kernel,
    num_samples=500,
    warmup_steps=500,
    num_chains=1,
    disable_progbar=True,
    disable_validation=False,  # keep validation enabled while developing
)
mcmc.run(data)
samples = mcmc.get_samples()
mcmc.summary(prob=0.9)
diag = mcmc.diagnostics()
```

Development runs can use tens of samples only to exercise code paths. Use far
more warmup and retained samples before interpreting posterior estimates.

## NUTS Versus HMC

Prefer `NUTS(model)` for new work because it adapts trajectory length by tree
doubling and usually needs fewer hand-tuned settings. Tune:

- `target_accept_prob`: default `0.8`; increase to `0.9` or `0.95` when
  divergences persist after shape/support fixes. Higher values use smaller step
  sizes and can be slower.
- `max_tree_depth`: default `10`; increase only if diagnostics suggest the tree
  is saturating and the model geometry is otherwise healthy. Deeper trees can be
  exponentially more expensive.
- `adapt_step_size=True` and `adapt_mass_matrix=True`: keep enabled for most
  models. Disable only for controlled experiments or when continuing from a
  carefully tuned kernel.
- `full_mass`: `False` uses diagonal mass. `True` uses one dense block over all
  latent sites. A list of tuples such as `[('alpha', 'beta')]` adapts dense
  blocks for selected correlated sites and diagonal mass for the rest.

Use `HMC(model, step_size=..., num_steps=...)` when a fixed trajectory is part of
the experiment or you are debugging a specific integrator configuration. If both
`trajectory_length` and `num_steps` are omitted, HMC uses a default trajectory
length derived from Stan-style practice; NUTS is usually easier.

## Initialization Strategies

HMC/NUTS operate internally in unconstrained coordinates, but a Pyro model is
written in constrained values such as positive scales or simplexes. For ordinary
`NUTS(model)` or `HMC(model)`, prefer `init_strategy` with constrained values:

```python
from pyro.infer.autoguide import init_to_feasible, init_to_mean, init_to_value

kernel = NUTS(
    model,
    init_strategy=init_to_value(
        values={
            "scale": torch.tensor(1.0),      # constrained positive value
            "loc": torch.tensor(0.0),
        },
        fallback=init_to_feasible,
    ),
)
```

Common strategies:

| Strategy | Best use | Caveat |
|---|---|---|
| `init_to_uniform(radius=2.0)` | Default; random values in unconstrained space. | Can fail for constrained or fragile likelihoods. |
| `init_to_feasible()` | Fast feasible point independent of distribution parameters. | May be far from posterior mass. |
| `init_to_sample()` | Sample from the prior. | Heavy-tailed or weak priors can produce invalid or slow starts. |
| `init_to_median(num_samples=15)` | Robust prior-centered scalar starts. | Falls back for multivariate or undefined medians. |
| `init_to_mean()` | Mean-centered starts when means are finite. | Falls back for distributions such as Cauchy-like priors. |
| `init_to_value(values={...})` | Known good constrained values or heuristic starts. | Values must match site names and constrained shapes. |
| `init_to_generated(generate=...)` | Different generated initial values across traces/chains. | Keep the generator deterministic if reproducibility matters. |

Use explicit `initial_params` only when you understand the unconstrained
coordinate system. For `num_chains > 1`, each tensor in `initial_params` must have
leading dimension `num_chains`. With a custom `potential_fn`, Pyro cannot infer
model sites or constrained supports; provide valid initial parameters and any
needed transforms yourself.

## Transforms And Constrained Supports

For model-based kernels, Pyro automatically creates transforms from constrained
site supports to unconstrained MCMC coordinates using the constraint registry.
Usually do not pass `transforms`.

Pass a `transforms` dict only when you need to override a site's automatic
transform or when constructing a kernel from a custom `potential_fn`. The dict is
keyed by site/parameter name and should map constrained values to unconstrained
values; Pyro calls `.inv(...)` to transform retained samples back before
`get_samples()`.

Checklist for transform issues:

1. Verify the latent distribution support in the distribution sibling skill.
2. Prefer `init_strategy=init_to_value(...)` with constrained values instead of
   hand-building `initial_params`.
3. If using `potential_fn`, test the potential and gradient on your
   `initial_params` before running long chains.
4. If retained samples are in the wrong domain, your custom transform likely has
   the wrong direction.

## Warmup, Samples, And Chains

A practical progression:

1. **Code smoke:** `num_samples=2..20`, `warmup_steps=2..20`,
   `disable_progbar=True`. Only checks that the model and kernel execute.
2. **Debug run:** `num_samples=100..300`, `warmup_steps=100..300`, validation on,
   one chain. Fix support, plate, divergence, and NaN issues.
3. **Inference run:** multiple chains when possible, enough warmup for adaptation,
   enough retained samples for target precision. Interpret diagnostics by site.

Chain behavior:

- `num_chains=1` uses a single-process sampler.
- `num_chains>1` uses multiprocessing only when enough CPU workers are available;
  otherwise Pyro warns and draws chains sequentially.
- Multiprocessing requires model and kernel state to be picklable. Define models
  and helpers at module top level when possible.
- For CUDA tensors, use `mp_context="spawn"`; CUDA is optional and was not part of
  the minimum verified runtime.
- `get_samples(group_by_chain=True)` returns tensors shaped
  `(num_chains, num_samples, ...)`; the default collapses chains to
  `(num_chains * num_samples, ...)`.

## Diagnostics Workflow

After `mcmc.run(...)`:

```python
samples_by_chain = mcmc.get_samples(group_by_chain=True)
summary = mcmc.summary(prob=0.9)
diag = mcmc.diagnostics()
```

Interpretation checklist:

- `divergences`: any nonzero post-warmup divergences need attention before
  trusting tail estimates. Increase `target_accept_prob`, improve initialization,
  reparameterize, or inspect support/shape errors.
- `acceptance rate`: very low rates usually indicate a too-large step size,
  invalid geometry, or initialization far from posterior mass. Very high rates
  can mean overly small steps and slow mixing.
- `n_eff`: compare by site and by component; low values mean high autocorrelation
  or too few independent draws.
- `r_hat`: values near 1 across chains are expected for well-mixed chains;
  large values suggest nonconvergence or chain-specific modes.
- `summary(prob=...)`: the credible interval probability controls HPDI columns;
  it does not change samples.

Use `save_params=[...]` to retain and diagnose only selected latent sites in
large models. Use `hook_fn(kernel, params, stage, i)` for custom per-step logging,
such as potential energy traces, but avoid mutating model state inside the hook.

## Eight-Schools Pattern

A compact hierarchical model uses a non-centered parameterization:

```python
def eight_schools_model(y=None, sigma=None):
    num_schools = sigma.numel()
    eta = pyro.sample(
        "eta",
        dist.Normal(sigma.new_zeros(num_schools), 1.0).to_event(1),
    )
    mu = pyro.sample("mu", dist.Normal(sigma.new_tensor(0.0), 10.0))
    tau = pyro.sample("tau", dist.HalfCauchy(sigma.new_tensor(25.0)))
    theta = pyro.deterministic("theta", mu + tau * eta, event_dim=1)
    with pyro.plate("school", num_schools, dim=-1):
        pyro.sample("obs", dist.Normal(theta, sigma), obs=y)
```

Run it with:

```python
kernel = NUTS(eight_schools_model, target_accept_prob=0.8, max_tree_depth=5)
mcmc = MCMC(kernel, num_samples=200, warmup_steps=200, disable_progbar=True)
mcmc.run(y, sigma)
samples = mcmc.get_samples()
```

The bundled smoke script implements this pattern with embedded data and tiny
defaults. Use it to verify package behavior, not to estimate a publication-grade
posterior.

## Discrete Latent Variables In MCMC

HMC/NUTS state is continuous. A model with a latent `Categorical`, `Bernoulli`,
integer count, or other enumerable site must be handled deliberately:

- observed discrete sites are fine;
- finite discrete sites can sometimes be enumerated out if plate dimensions and
  `max_plate_nesting` are correct;
- complex discrete state-space models often need reparameterization,
  `config_enumerate`, `infer_discrete`, or a different inference algorithm;
- subsampled data plates are not supported by HMC/NUTS model initialization.

When the user's problem is really enumeration dimension allocation, handler
ordering, or posterior decoding of discrete states, route to
`../effect-handlers-and-enumeration/` rather than inventing continuous initial
values for discrete sites.
