# ZhuSuan overview

ZhuSuan is a TensorFlow 1.x probabilistic-programming library for Bayesian deep
learning. The core workflow is to build a probabilistic graph with
`BayesianNet` / `MetaBayesianNet`, then train or sample it with variational or
MCMC-style inference.

## Main module families

- `zhusuan.distributions`: reusable probability distributions and shape rules
- `zhusuan.framework`: `BayesianNet`, `StochasticTensor`, `MetaBayesianNet`
- `zhusuan.variational`: ELBO, IWAE, inclusive KL, and importance-based bounds
- `zhusuan.hmc` and `zhusuan.sgmcmc`: posterior samplers
- `zhusuan.evaluation`: importance-sampling likelihood estimation and AIS
- `zhusuan.transform`: normalizing-flow helpers
- `zhusuan.diagnostics`: chain-quality metrics

## Reading order

1. Read `sub-skills/modeling-primitives/SKILL.md` when you need to define the
   probabilistic graph itself.
2. Read `sub-skills/variational-inference/SKILL.md` when you need ELBO/IWAE
   training or flow-based variational posteriors.
3. Read `sub-skills/mcmc-and-sampling/SKILL.md` when you need HMC, SG-MCMC, or
   AIS.

## Quick install note

This repository targets a TF1-compatible Python environment. The verified
inspection environment used Python 3.6 with TensorFlow 1.15.5, SciPy, and mock.

## Quick smoke

Run `scripts/core_smoke.py` after install if you want a very small import and
objective check without touching the heavier example scripts.
