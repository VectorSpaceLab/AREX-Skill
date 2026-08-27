---
name: svi-autoguides
description: "Fit and debug NumPyro stochastic variational inference workflows
  with ELBOs, manual guides, autoguides, optimizers, and enumeration choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# svi-autoguides

Use this sub-skill when the task is to fit a NumPyro model with stochastic variational inference (SVI), write or repair a guide, choose an ELBO, use automatic guides, inspect learned parameters and losses, handle discrete latent variables in SVI, or turn SVI results into posterior/predictive samples.

## Quick workflow

1. **Confirm model and guide signatures.** Model/guide primitive and shape issues route through [../modeling-primitives/](../modeling-primitives/) and distribution support issues through [../distributions-transforms/](../distributions-transforms/).
2. **Choose a guide path.** Use a manual guide for custom variational families or constraints; use [references/autoguide-reference.md](references/autoguide-reference.md) for `AutoNormal`, `AutoDelta`, normal-family autoguides, Laplace, flow guides, DAIS, and guide lists.
3. **Choose an ELBO.** Use [references/elbo-and-enumeration.md](references/elbo-and-enumeration.md) for `Trace_ELBO`, `TraceMeanField_ELBO`, `TraceGraph_ELBO`, `TraceEnum_ELBO`, `RenyiELBO`, and discrete enumeration.
4. **Run SVI.** Use [references/svi-workflows.md](references/svi-workflows.md) for `SVI.init`, `update`, `run`, `get_params`, `evaluate`, optimizer selection, and posterior predictive use.
5. **Validate losses and params.** Check finite losses, constrained parameter values, expected keys, and posterior predictive shapes.
6. **Run the bundled smoke.** [scripts/svi_smoke.py](scripts/svi_smoke.py) is a small synthetic SVI check adapted from NumPyro's minimal example.
7. **Triage failures.** Use [references/troubleshooting.md](references/troubleshooting.md) for NaN losses, invalid guide values, wrong ELBO for discrete sites, missing `optax`/`funsor`, and local-latent guide limitations.

## Prefer this sub-skill for

- `SVI(model, guide, optim, loss)` setup and update loops.
- `Trace_ELBO`, `TraceMeanField_ELBO`, `TraceGraph_ELBO`, `TraceEnum_ELBO`, or `RenyiELBO` decisions.
- `numpyro.param` constraints in guides.
- `AutoNormal`, `AutoDiagonalNormal`, `AutoMultivariateNormal`, `AutoLowRankMultivariateNormal`, `AutoDelta`, `AutoGuideList`, `AutoLaplaceApproximation`, `AutoIAFNormal`, `AutoBNAFNormal`, `AutoDAIS`, `AutoSemiDAIS`, and `AutoSurrogateLikelihoodDAIS`.
- Discrete enumeration with `config_enumerate`, `infer={"enumerate": "parallel"}`, and `TraceEnum_ELBO`.
- Optimizer selection with `numpyro.optim` or optional Optax optimizers.

## Route elsewhere when

- The task is MCMC/NUTS/HMC, chain diagnostics, divergences, or posterior samples from MCMC: use [../mcmc-diagnostics/](../mcmc-diagnostics/).
- The task is a core model/handler/plate trace before fitting: use [../modeling-primitives/](../modeling-primitives/).
- The task is distribution constructor/support/transform shape semantics: use [../distributions-transforms/](../distributions-transforms/).
- The task is SteinVI/SVGD/ASVGD, Funsor internals, neural module wrappers, nested sampling, HSGP, or TFP: use [../advanced-contrib/](../advanced-contrib/).

## Bundled materials

- [SVI workflows](references/svi-workflows.md) covers manual guides, loops, params, losses, and predictive use.
- [Autoguide reference](references/autoguide-reference.md) maps guide families to task signals and caveats.
- [ELBO and enumeration](references/elbo-and-enumeration.md) explains loss selection and discrete latent handling.
- [Troubleshooting](references/troubleshooting.md) gives symptom-to-fix guidance.
- [SVI smoke script](scripts/svi_smoke.py) validates a tiny synthetic variational fit.
