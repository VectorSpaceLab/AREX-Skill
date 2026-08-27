---
name: variational-inference
description: "Use ZhuSuan for ELBO, IWAE, inclusive KL, importance-sampling
  likelihoods, normalizing flows, and VAE/BNN/SVGP-style variational workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Variational Inference

Use this sub-skill when the task is about learning latent-variable models with
ELBO-style or importance-weighted objectives.

## Read this when

- the user names `elbo`, `importance_weighted_objective`, `klpq`, `is_loglikelihood`,
  `sgvb`, `reinforce`, `vimco`, `RWS`, `IWAE`, `VAE`, `BNN`, or `SVGP`
- the task is about variational posteriors, multi-sample objectives, or
  importance-sampling based marginal likelihood estimates
- the user wants to stack normalizing flows onto a variational distribution
- the request is about semi-supervised VAE or sigmoid-belief-network examples

## What this sub-skill owns

- ELBO, inclusive KL, and importance-weighted objectives
- gradient estimators: SGVB, REINFORCE, VIMCO, and importance-sampling wake-sleep
- `is_loglikelihood` for marginal log-likelihood estimation
- normalizing flows: planar and inverse autoregressive flows
- the variational example families: VAE, BNN, semi-supervised VAE, SBN, and SVGP

## What this sub-skill does not own

- HMC, SGLD, SGHMC, SGNHT, AIS, or sampling diagnostics
- core Bayesian-network modeling basics
- generic TensorFlow training unrelated to probabilistic inference

## Start here

1. Read `references/variational-workflows.md` for the workflow map.
2. Read `references/api-reference.md` for exact objective and flow signatures.
3. Read `references/troubleshooting.md` for common estimator and axis mistakes.
4. Run `scripts/vi_smoke.py` after environment setup to check ELBO, IWAE,
   importance-sampling likelihood, flows, and the GP helper path.

## Common tasks

### Train a VAE / BNN / SVGP

- Build a generative `MetaBayesianNet` with latent variables and observations.
- Build a variational `BayesianNet` that produces the latent samples and their
  log probabilities.
- Use `zs.variational.elbo(...)` or
  `zs.variational.importance_weighted_objective(...)`.
- Optimize `lower_bound.sgvb()` for reparameterized latents, or
  `lower_bound.reinforce()` / `lower_bound.vimco()` when the latent variables
  are not reparameterizable.

### Add normalizing flows

- Pull the latent samples and log probabilities from `q_net.query(...)`.
- Pass them through `planar_normalizing_flow(...)` or
  `inv_autoregressive_flow(...)`.
- Feed the transformed samples and adjusted log probabilities back into the
  variational objective.

### Estimate marginal log likelihood

- Use `zs.is_loglikelihood(...)` with the same latent samples and proposal as
  the variational model.
- Remember that importance-sampling estimates are only as good as the proposal;
  they are often used as evaluation metrics, not as the main training target.

## Good entry points

- `zhusuan/variational/base.py`
- `zhusuan/variational/exclusive_kl.py`
- `zhusuan/variational/inclusive_kl.py`
- `zhusuan/variational/monte_carlo.py`
- `zhusuan/evaluation.py`
- `zhusuan/transform.py`
- `scripts/vi_smoke.py`
- `sub-skills/variational-inference/scripts/gp_helpers.py`

## Routing hints

- If the request is only about the core probabilistic graph, route to
  `modeling-primitives`.
- If the request is about posterior sampling, route to `mcmc-and-sampling`.
- If the task is about training scripts that merely use TensorFlow optimizers
  without a probabilistic objective, a non-ZhuSuan skill may fit better.
