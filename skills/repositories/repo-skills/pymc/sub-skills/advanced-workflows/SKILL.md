---
name: advanced-workflows
description: "Apply PyMC Gaussian processes, ODE likelihood models, variational
  inference, minibatches, and experimental dimensional APIs at a practical
  workflow level."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyMC advanced workflows

Use this sub-skill when a PyMC task involves Gaussian processes, ODE likelihoods, variational inference/OPVI, minibatches, or experimental dimension-aware APIs in advanced models.

## Read/run map

- Read [references/gaussian-processes.md](references/gaussian-processes.md) when choosing `pm.gp` means/covariances, `Latent`, `Marginal`, sparse/marginal approximations, HSGP, or GP conditionals.
- Read [references/ode-workflows.md](references/ode-workflows.md) when building `pm.ode.DifferentialEquation` likelihood models or debugging `func`, `times`, `y0`, `theta`, `n_states`, and `n_theta` shapes.
- Read [references/variational-inference.md](references/variational-inference.md) when using `pm.fit`, `ADVI`, `FullRankADVI`, `SVGD`/`ASVGD`, callbacks, `sample_approx`, or `pm.Minibatch`.
- Read [references/troubleshooting.md](references/troubleshooting.md) for GP shapes, ODE return types, VI convergence, minibatch scaling, or approximation failures.
- Run [scripts/advanced_workflows_smoke.py](scripts/advanced_workflows_smoke.py) to check tiny CPU-only GP, ODE, and VI workflows.

Route ordinary model/data syntax to `../modeling-data/SKILL.md`, distribution/logp internals to `../distributions-logprob/SKILL.md`, and standard MCMC/predictive outputs to `../inference-predictive/SKILL.md`.

## Operating procedure

1. Identify the advanced family first: GP, ODE, VI/minibatch, or experimental dims interaction.
2. Build only the family-specific model component here; pull base model/data and likelihood details from siblings when needed.
3. Choose inference deliberately. Prefer ordinary `pm.sample` for final posterior quality when feasible; use VI for fast approximate fitting, initialization, large data/minibatches, or exploratory checks.
4. Add the smallest possible smoke check: GP covariance or conditional shape, ODE forward simulation shape, or low-iteration VI fit plus approximation sample.
