# MCMC workflows

This reference covers the operating workflow for NumPyro's `MCMC` wrapper and kernels. It assumes the model itself is already written; route model syntax questions to [../../modeling-primitives/](../../modeling-primitives/).

## Minimal NUTS workflow

```python
from jax import random
from numpyro.infer import MCMC, NUTS
from numpyro.infer.initialization import init_to_median

kernel = NUTS(
    model,
    target_accept_prob=0.9,          # raise for fewer divergences, slower sampling
    dense_mass=False,                # or a block list such as [("alpha", "beta")]
    init_strategy=init_to_median(),
)
mcmc = MCMC(
    kernel,
    num_warmup=1_000,
    num_samples=2_000,
    num_chains=4,
    chain_method="parallel",          # see backend/chain reference
    progress_bar=True,
)
mcmc.run(
    random.key(0),
    *model_args,
    **model_kwargs,
    extra_fields=("potential_energy", "num_steps", "adapt_state.step_size"),
)
samples_by_chain = mcmc.get_samples(group_by_chain=True)
extra_by_chain = mcmc.get_extra_fields(group_by_chain=True)
mcmc.print_summary(prob=0.9)
```

For real inference, choose warmup/samples from the problem rather than from smoke examples. Tiny runs prove plumbing only.

## Kernel choice guide

| Kernel | Use when | Key constraints and knobs |
| --- | --- | --- |
| `NUTS(model)` | Default for differentiable continuous latent-variable models. It adapts path length and mass matrix. | `target_accept_prob`, `dense_mass`, `max_tree_depth`, `init_strategy`, `forward_mode_differentiation`. Can enumerate finite discrete sites when they are marked for parallel enumeration and enumeration is tractable. |
| `HMC(model)` | You need fixed integration control or are using `MixedHMC`. | `num_steps` or `trajectory_length`; specifying both while adapting step size prevents step-size adaptation. Same mass/init knobs as NUTS. |
| `BarkerMH(model)` | Low/moderate-dimensional differentiable targets where Barker proposals may be competitive. | Gradient-based; default `target_accept_prob=0.4`; use `progress_bar=False` if dispatch overhead dominates. Does not support `chain_method="vectorized"`. |
| `DiscreteHMCGibbs(NUTS(model))` | Finite discrete latent sites should be sampled instead of enumerated. | Detects non-observed discrete sites with enumerable support. Use `modified=True` for a Metropolised Gibbs variant. |
| `MixedHMC(HMC(model))` | Mixed continuous/discrete models where mixed HMC is preferred. | Inner kernel must be `HMC`, not `NUTS`; `num_discrete_updates` controls discrete updates. |
| `HMCGibbs(NUTS(model), gibbs_fn, gibbs_sites)` | You can write an exact or custom Gibbs updater for selected latent sites. | `gibbs_fn(rng_key, gibbs_sites, hmc_sites)` must return a dict for all `gibbs_sites`. |
| `HMCECS(NUTS(model), num_blocks, proxy)` | Large factorized likelihood with `plate(..., subsample_size=...)`. | Experimental. Requires detectable subsample plates. A `taylor_proxy` needs reference parameters; if those come from SVI, route the guide-training step to [../../svi-autoguides/](../../svi-autoguides/). |
| `SA(model)` | Gradient-free fallback for continuous, low/moderate-dimensional or non-differentiable targets. | Often needs very large warmup/sample counts; default dense mass; use `progress_bar=False` for speed. |
| `AIES(model)` | Gradient-free affine-invariant ensemble sampling for low/moderate dimension. | Must use `num_chains > 1`, even chain count, and `chain_method="vectorized"`; at least `2 * latent_dim` chains is strongly recommended. |
| `ESS(model)` | Gradient-free ensemble slice sampling; often more sample-efficient than AIES. | Same vectorized/even-chain constraints as AIES; choose moves such as `ESS.DifferentialMove()` or `ESS.RandomMove()`. |

Nested sampling, SteinVI, and TFP contrib kernels are not owned here; route them to [../../advanced-contrib/](../../advanced-contrib/).

## Important constructor signatures

Observed for the generated skill's NumPyro API surface:

- `MCMC(sampler, *, num_warmup, num_samples, num_chains=1, thinning=1, postprocess_fn=None, chain_method='parallel', progress_bar=True, progress_rate=None, jit_model_args=False)`
- `NUTS(model=None, potential_fn=None, kinetic_fn=None, step_size=1.0, inverse_mass_matrix=None, adapt_step_size=True, adapt_mass_matrix=True, dense_mass=False, target_accept_prob=0.8, trajectory_length=None, max_tree_depth=10, init_strategy=init_to_uniform, find_heuristic_step_size=False, forward_mode_differentiation=False, regularize_mass_matrix=True)`
- `HMC(..., num_steps=None, trajectory_length=2*pi, ...)`
- `Predictive(model, posterior_samples=None, *, guide=None, params=None, num_samples=None, return_sites=None, infer_discrete=False, parallel=False, batch_ndims=None, exclude_deterministic=True)`
- `log_likelihood(model, posterior_samples, *args, parallel=False, batch_ndims=1, **kwargs)`

## Setup, run, sample, postprocess

1. **Set backend and chain layout early.** If the workflow needs CPU parallel chains, call `numpyro.set_host_device_count(num_chains)` before the first JAX computation. See [backend-and-chain-configuration.md](backend-and-chain-configuration.md).
2. **Pick an initialization strategy.** Default `init_to_uniform()` is robust for many models, but `init_to_median()`, `init_to_mean()`, `init_to_feasible()`, or `init_to_value(values={...})` can rescue invalid starts.
3. **Choose adaptation knobs.** For NUTS/HMC, raise `target_accept_prob` (for example from `0.8` to `0.9` or `0.95`) when divergences occur; use `dense_mass=True` or block lists when posterior correlations are strong and dimensionality permits.
4. **Run with diagnostic fields.** Useful fields include `potential_energy`, `diverging`, `num_steps`, `accept_prob`, `mean_accept_prob`, and nested fields such as `adapt_state.step_size`. HMC-family kernels collect `diverging` by default.
5. **Preserve chain dimension for diagnostics.** Use `get_samples(group_by_chain=True)` and `get_extra_fields(group_by_chain=True)` when computing `r_hat`, ESS, or per-chain summaries.
6. **Flatten only for downstream posterior use.** `get_samples()` without `group_by_chain` flattens `num_chains * num_samples` into the leading dimension; this is usually the right layout for `Predictive` and `log_likelihood` with `batch_ndims=1`.
7. **Transfer to host for memory pressure.** After a large run, `mcmc.transfer_states_to_host()` reduces device memory held by collected states.

## Warmup reuse and repeated runs

Use `MCMC.warmup(...)` when you want to adapt once and sample later:

```python
mcmc = MCMC(NUTS(model), num_warmup=1_000, num_samples=1_000)
mcmc.warmup(random.key(0), *model_args, collect_warmup=False)
# Later, with the same model/data shapes:
mcmc.run(random.key(1), *model_args)
```

`mcmc.post_warmup_state` stores the adapted state. You can also set `mcmc.post_warmup_state = mcmc.last_state` to continue sampling sequentially from the previous final state. Re-run warmup when the model structure or data shape changes. `jit_model_args=True` can reduce recompilation when repeatedly running the same model on same-shaped but different-valued arguments; it does not help all parallel-chain cases.

## Dense mass and structured mass matrices

- `dense_mass=False` uses a diagonal mass matrix for all latent sites.
- `dense_mass=True` uses one dense block over all latent sites when a model is supplied.
- `dense_mass=[("x", "y")]` uses a dense block for named sites `x,y` and diagonal mass for the rest.
- `dense_mass=[("x",), ("y",)]` uses separate dense blocks per site.

Dense blocks can improve mixing for correlated parameters but increase warmup cost and memory. Prefer small blocks for known correlated groups; use summaries and divergences to decide whether the added cost helped.

## Potential-function workflows

Kernels can be constructed with `potential_fn` instead of `model` when you already have an unconstrained log-density function:

```python
kernel = NUTS(potential_fn=lambda z: potential_energy_value)
mcmc = MCMC(kernel, num_warmup=500, num_samples=1_000)
mcmc.run(random.key(0), init_params=initial_pytree)
```

When using `potential_fn`, `init_params` is required and samples are returned with the same pytree structure as the initial parameters. Model-backed workflows are usually easier because NumPyro handles constraints and deterministic sites.
