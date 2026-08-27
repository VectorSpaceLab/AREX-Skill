# Diagnostics and reparameterization

MCMC output is only useful after diagnostics show that chains explored the posterior reasonably for the task. Use tiny runs for plumbing; use enough warmup/samples/chains for scientific conclusions.

## What to collect

```python
mcmc.run(
    rng_key,
    *model_args,
    **model_kwargs,
    extra_fields=("potential_energy", "diverging", "num_steps", "adapt_state.step_size"),
)
samples = mcmc.get_samples(group_by_chain=True)
extra = mcmc.get_extra_fields(group_by_chain=True)
mcmc.print_summary(prob=0.9)
```

Useful outputs:

| Signal | Meaning | First response |
|---|---|---|
| `diverging` | HMC trajectory encountered numerical/geometry failure. | Increase `target_accept_prob`, inspect priors/scales, reparameterize, or enable x64. |
| `r_hat` / split Gelman-Rubin | Between-chain versus within-chain mixing. Values near 1 are desired. | Run more warmup/samples/chains, improve geometry, check multimodality. |
| `n_eff` / ESS | Effective independent sample count. | Increase samples or improve sampler geometry; do not rely only on raw sample count. |
| `num_steps` | NUTS tree size/trajectory effort. | Very high values suggest difficult geometry or too-small step size. |
| `adapt_state.step_size` | Adapted HMC step size. | Very small values often indicate poor scaling or sharp posterior geometry. |
| `potential_energy` | Energy trajectory; used for energy diagnostics and expected log joint. | Non-finite or extreme values point to bad initialization/model support issues. |

## Summary helpers

NumPyro includes diagnostic helpers in `numpyro.diagnostics`:

- `summary(samples, prob=0.9, group_by_chain=True)`
- `print_summary(samples, prob=0.9, group_by_chain=True)`
- `effective_sample_size`, `gelman_rubin`, `split_gelman_rubin`, `hpdi`, `autocorrelation`, `autocovariance`

`MCMC.print_summary()` is usually the quickest route for MCMC objects.

## Divergence triage

1. **Check the model and support.** Trace a tiny conditioned run in `../modeling-primitives/` and validate distribution parameters in `../distributions-transforms/`.
2. **Increase target acceptance.** Try `NUTS(model, target_accept_prob=0.9)` or `0.95`.
3. **Use stronger initialization.** Try `init_to_median()`, `init_to_feasible()`, or `init_to_value(values={...})`.
4. **Reparameterize hierarchical or constrained sites.** Use `LocScaleReparam`, `TransformReparam`, `NeuTraReparam`, or an explicit non-centered model.
5. **Consider dense mass.** Use `dense_mass=True` or named blocks for strongly correlated latents if dimension and memory permit.
6. **Enable x64** when numerical precision is suspect.
7. **Reconsider the model.** Very heavy tails, weak identification, separation, or funnel geometry may require stronger priors or a different parameterization.

## Non-centered and loc-scale reparameterization

For a hierarchical latent `theta ~ Normal(mu, tau)`, a non-centered form often improves geometry. Explicit form:

```python
base = numpyro.sample("theta_base", dist.Normal(0, 1).expand((J,)))
theta = numpyro.deterministic("theta", mu + tau * base)
```

Handler form:

```python
from numpyro import handlers
from numpyro.infer.reparam import LocScaleReparam

with handlers.reparam(config={"theta": LocScaleReparam(centered=0.0)}):
    theta = numpyro.sample("theta", dist.Normal(mu, tau))
```

`centered=0.0` is fully non-centered; `centered=1.0` is centered; intermediate values can be learned or chosen.

## `TransformReparam`

Use when sampling from a `TransformedDistribution` and HMC should operate on the base distribution:

```python
from numpyro.infer.reparam import TransformReparam

with numpyro.handlers.reparam(config={"theta": TransformReparam()}):
    theta = numpyro.sample("theta", transformed_distribution)
```

This is useful when a transformed support creates difficult geometry. Validate the transform itself in `../distributions-transforms/`.

## `NeuTraReparam`

`NeuTraReparam` uses a trained autoguide transform to reparameterize MCMC. Workflow:

1. Train an appropriate guide with SVI in `../svi-autoguides/`.
2. Construct `NeuTraReparam(guide, params)` from the trained guide/params.
3. Reparameterize the model and run MCMC here.

Use this for hard continuous posteriors only after a guide trains reliably. If SVI losses are unstable, fix the SVI workflow before running NeuTra MCMC.

## Discrete latent variables

- NUTS/HMC cannot directly sample arbitrary discrete latent variables.
- For finite discrete sites, mark `infer={"enumerate": "parallel"}` when enumeration is tractable.
- Use `DiscreteHMCGibbs(NUTS(model))` when you want Gibbs updates for enumerable discrete sites.
- Use `MixedHMC(HMC(model))` for mixed continuous/discrete HMC when appropriate.
- Discrete enumeration with `TraceEnum_ELBO` and Funsor belongs in `../svi-autoguides/` and `../advanced-contrib/`.

## Reporting diagnostics

When handing results to a user, include:

- Model/data shape and key inference settings (`kernel`, `num_warmup`, `num_samples`, `num_chains`, `chain_method`, x64/backend).
- Summary of divergences and max/typical `r_hat`/ESS.
- Whether samples were grouped by chain for diagnostics.
- Any reparameterization, initialization, dense mass, or target-accept changes tried.
- Clear stop condition if diagnostics remain poor.
