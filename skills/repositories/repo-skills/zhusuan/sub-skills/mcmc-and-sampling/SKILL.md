---
name: mcmc-and-sampling
description: "Use ZhuSuan for HMC, SGLD, PSGLD, SGHMC, SGNHT, annealed
  importance sampling, and posterior-sampling diagnostics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# MCMC and Sampling

Use this sub-skill when the task is about posterior sampling or sampling-based
estimation rather than variational training.

## Read this when

- the user names `HMC`, `SGLD`, `PSGLD`, `SGHMC`, `SGNHT`, `AIS`, or `effective_sample_size`
- the task is about sampling latent variables, posterior chains, or sampling
  diagnostics
- the request mentions toy posterior examples, topic models, or matrix
  factorization examples that use HMC or stochastic-gradient MCMC

## What this sub-skill owns

- `HMC.sample(...)` and the HMC adaptation knobs
- stochastic-gradient MCMC classes: `SGLD`, `PSGLD`, `SGHMC`, `SGNHT`
- `AIS` for annealed importance sampling over a sequence of temperatures
- `effective_sample_size` diagnostics for chain quality
- toy examples and heavier sampling workflows such as PMF and topic models

## What this sub-skill does not own

- core Bayesian-network construction
- ELBO / IWAE / VIMCO / REINFORCE / flow-based variational workflows
- generic training code that does not use a ZhuSuan sampler

## Start here

1. Read `references/mcmc-workflows.md` for the sampler map and example matrix.
2. Read `references/api-reference.md` for exact constructor and sample
   signatures.
3. Read `references/troubleshooting.md` for adaptation, acceptance, and chain
   shape issues.
4. Run `scripts/mcmc_smoke.py` after environment setup to confirm a short HMC
   chain, sampler instantiation, and ESS calculation.

## Common tasks

### Run HMC

- Build a `log_joint` function or pass a `MetaBayesianNet`.
- Create TensorFlow `Variable` objects to hold the latent state.
- Instantiate `zs.HMC(...)` with a small step size and a handful of leapfrog
  steps.
- Call `sample(meta_bn, observed, latent)` once per sampler instance.
- Turn adaptation on only during burn-in.

### Run stochastic-gradient MCMC

- Use `zs.SGLD`, `zs.SGHMC`, or `zs.SGNHT` when the gradient is minibatch-
  based.
- Keep the latent variables in `Variable` objects and feed minibatches into the
  observed data placeholders.
- For SGHMC and SGNHT, watch the kinetic-energy / friction diagnostics.

### Evaluate a chain

- Flatten the chain to a 2-D matrix when using `effective_sample_size`.
- For multiple chains or latent dimensions, keep track of the axis ordering so
  the diagnostic matches the intended latent dimension.

## Good entry points

- `zhusuan/hmc.py`
- `zhusuan/sgmcmc.py`
- `zhusuan/evaluation.py` for AIS
- `zhusuan/diagnostics.py`
- `scripts/mcmc_smoke.py`

## Routing hints

- If the request is about a Bayesian model but not about sampling, route to
  `modeling-primitives`.
- If the request is about a variational posterior or a lower bound, route to
  `variational-inference`.
- If the user asks about a plotting-heavy toy example, treat it as a workflow
  reference rather than a required verification target unless the user
  explicitly wants the demo run.
