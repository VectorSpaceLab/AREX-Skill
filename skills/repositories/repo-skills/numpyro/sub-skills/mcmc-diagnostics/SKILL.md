---
name: mcmc-diagnostics
description: "Run and troubleshoot NumPyro MCMC workflows with diagnostics,
  predictive sampling, reparameterization, and JAX chain configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# mcmc-diagnostics

Use this sub-skill when the task is to run, configure, inspect, or repair a NumPyro MCMC workflow: NUTS/HMC, alternative kernels, multiple chains, diagnostics, posterior predictive sampling, pointwise log likelihood, bad-geometry fixes, or JAX backend selection.

## Quick workflow

1. Choose a kernel and MCMC layout from [references/mcmc-workflows.md](references/mcmc-workflows.md).
2. Configure the backend and chains before the first JAX computation using [references/backend-and-chain-configuration.md](references/backend-and-chain-configuration.md).
3. Run `MCMC.run(...)` with useful `extra_fields`, then inspect `get_samples(...)`, `get_extra_fields(...)`, and `print_summary(...)`.
4. Diagnose `diverging`, `potential_energy`, low `n_eff`, high `r_hat`, and weak ESS using [references/diagnostics-and-reparameterization.md](references/diagnostics-and-reparameterization.md).
5. Generate posterior predictive samples or log likelihood arrays with [references/predictive-loglikelihood.md](references/predictive-loglikelihood.md).
6. If execution or diagnostics fail, use [references/troubleshooting.md](references/troubleshooting.md).

## Bundled smoke script

Run the CPU-safe 8-schools smoke test when you need a deterministic sanity check of NUTS, diagnostics fields, and optional posterior predictive sampling:

```bash
python scripts/eight_schools_smoke.py --help
python scripts/eight_schools_smoke.py --num-warmup 20 --num-samples 30 --predict-new-school
```

The script uses tiny defaults for fast validation only; do not treat its diagnostics as convergence evidence for a real analysis.

## Routing and boundaries

- Model primitives, plates, handlers, and observation-site basics belong in [../modeling-primitives/](../modeling-primitives/).
- Distribution shape/support details and transform catalogs belong in [../distributions-transforms/](../distributions-transforms/).
- SVI, autoguides, and the prefit phase needed before `NeuTraReparam` belong in [../svi-autoguides/](../svi-autoguides/); return here for NeuTra-backed MCMC after a guide is trained.
- Optional nested sampling, SteinVI, and other contrib inference routes belong in [../advanced-contrib/](../advanced-contrib/).

## Prefer this sub-skill for

- Selecting between `NUTS`, `HMC`, `BarkerMH`, `MixedHMC`, `HMCGibbs`, `DiscreteHMCGibbs`, `HMCECS`, `SA`, `AIES`, and `ESS`.
- Using `MCMC.run`, `warmup`, `post_warmup_state`, `get_samples`, `get_extra_fields`, and `print_summary`.
- Collecting `potential_energy`, `diverging`, `num_steps`, `accept_prob`, or `adapt_state.step_size`.
- Applying `TransformReparam`, `LocScaleReparam`, or `NeuTraReparam` to reduce bad posterior geometry.
- Explaining `num_chains`, `chain_method`, CPU host devices, GPU/TPU backend selection, and x64 precision.
