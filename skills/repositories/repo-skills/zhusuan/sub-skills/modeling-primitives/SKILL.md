---
name: modeling-primitives
description: "Use ZhuSuan's distributions, BayesianNet, MetaBayesianNet, and
  stochastic tensor primitives to build and inspect probabilistic models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Modeling Primitives

Use this sub-skill when the task is about ZhuSuan's core probabilistic-modeling
surface rather than a specific inference algorithm.

## Read this when

- the user names `BayesianNet`, `MetaBayesianNet`, `StochasticTensor`,
  `meta_bayesian_net`, `reuse_variables`, `cond_log_prob`, `log_joint`,
  `query`, or `get`
- the task is about distributions, observed nodes, latent nodes, node naming,
  `group_ndims`, `n_samples`, or shape semantics
- the user wants to understand how to build a model graph before training or
  sampling
- the request is about compatibility or migration from the deprecated legacy
  wrappers

## What this sub-skill owns

- `zhusuan.distributions` and the `BayesianNet.<distribution>` helpers
- `BayesianNet`, `StochasticTensor`, `MetaBayesianNet`, and
  `meta_bayesian_net`
- observed-vs-latent node handling, deterministic nodes, and custom
  `log_joint`
- tensor-like behavior of stochastic nodes and shape checking rules
- safe use of `get`, `query`, `cond_log_prob`, and `log_joint`

## What this sub-skill does not own

- ELBO/IWAE/VIMCO/RWS, importance sampling likelihoods, or flows
- HMC, SGMCMC, AIS, or sampling diagnostics
- dataset downloads, example training loops, or plotting utilities

## Start here

1. Read `references/modeling-concepts.md` for the modeling rules and shape
   semantics.
2. Read `references/api-reference.md` when you need exact constructor or method
   signatures.
3. Read `references/troubleshooting.md` for dtype, shape, and deprecation
   issues.
4. Run `scripts/core_smoke.py` after environment setup to confirm the core
   package can build a tiny model and evaluate an ELBO.

## Common tasks

### Build a probabilistic model

- Create a `BayesianNet`.
- Add stochastic nodes with distribution helpers such as `normal`,
  `bernoulli`, `categorical`, `dirichlet`, or `multivariate_normal_cholesky`.
- Use deterministic TensorFlow ops for hidden calculations and optionally wrap
  them with `bn.deterministic(...)` when you want the node name tracked.

### Reuse a model with different observations

- Wrap the model builder with `@zs.meta_bayesian_net(scope=..., reuse_variables=True)`
  when repeated observation patterns should share TensorFlow variables.
- Call `model.observe(...)` to instantiate a concrete `BayesianNet` with a
  specific observation map.

### Inspect a network

- Use `bn.get(...)` to fetch nodes by name.
- Use `bn.cond_log_prob(...)` to inspect per-node conditional log probabilities.
- Use `bn.log_joint()` for the overall joint log probability.
- Use `bn.query(..., outputs=True, local_log_prob=True)` only when maintaining
  older code that still expects the deprecated tuple return.

## Good entry points

- `zhusuan/framework/bn.py`
- `zhusuan/framework/meta_bn.py`
- `zhusuan/distributions/base.py`
- `zhusuan/distributions/univariate.py`
- `zhusuan/distributions/multivariate.py`
- `scripts/core_smoke.py`

## Routing hints

- If the request is really about training a VAE/BNN or estimating posterior
  bounds, route to `variational-inference`.
- If the request is about HMC, SGHMC, SGNHT, or posterior sampling, route to
  `mcmc-and-sampling`.
- If the request is only about a generic TensorFlow model unrelated to
  probabilistic nodes or Bayesian inference, a different repo skill is likely a
  better fit.
