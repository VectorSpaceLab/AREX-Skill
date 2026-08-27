---
name: mcmc-and-prediction
description: "Run Pyro HMC/NUTS/MCMC diagnostics and prior/posterior predictive
  sampling workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MCMC And Prediction

Use this sub-skill when the user is running, tuning, or debugging Pyro
Hamiltonian Monte Carlo workflows (`NUTS`, `HMC`, `MCMC.run()`,
`get_samples()`, `summary()`, `diagnostics()`) or drawing prior/posterior
predictive samples with `Predictive`, `WeighedPredictive`, or `MHResampler`.

## Route First

- For NUTS/HMC setup, warmup/sample/chain choices, constrained-site
  initialization, transforms, diagnostics, and the eight-schools pattern, read
  [references/mcmc-workflows.md](references/mcmc-workflows.md).
- For prior predictive, posterior predictive from MCMC samples, deterministic
  and observed return sites, sample shapes, guide-based predictive, weighted
  predictive, and resampling, read
  [references/prediction-workflows.md](references/prediction-workflows.md).
- For divergences, invalid initial parameters/support, max tree depth,
  multiprocessing chains, memory, discrete latent variables, progress bars, JIT,
  and predictive shape surprises, read
  [references/troubleshooting.md](references/troubleshooting.md).
- To confirm that a small self-contained CPU NUTS workflow runs in the active
  package environment, run
  [scripts/eight_schools_mcmc_smoke.py](scripts/eight_schools_mcmc_smoke.py).
  Start with `python scripts/eight_schools_mcmc_smoke.py --help`; use
  `--disable-progbar` in non-interactive logs.

## Best-Fit Tasks

Use this sub-skill for requests like:

- "run NUTS/HMC on this Pyro model";
- "choose `num_samples`, `warmup_steps`, `num_chains`, or `target_accept_prob`";
- "initialize a positive/simplex/bounded latent site for MCMC";
- "read `mcmc.summary()` or `mcmc.diagnostics()` and fix divergences";
- "draw posterior predictive samples for observations or deterministic sites";
- "use `Predictive` with MCMC samples, an SVI guide, weighted samples, or
  `MHResampler`".

## Boundaries And Reroutes

- Model primitives, `pyro.sample`, `pyro.param`, `pyro.plate`, observations,
  `pyro.deterministic`, seeds, and parameter-store basics: route to
  `../modeling-basics/`.
- Distribution choice, support constraints, `.to_event()`, and detailed
  batch/event/plate shape algebra: route to `../distributions-and-shapes/`.
- SVI training, ELBO choice, autoguides, optimizers, and guide fitting before
  guide-based predictive: route to `../svi-and-autoguides/`.
- Handler ordering for `condition`, `replay`, `trace`, `block`, masking/scaling,
  `config_enumerate`, `infer_discrete`, and enumeration dimension allocation:
  route to `../effect-handlers-and-enumeration/`.
- Long domain examples such as epidemiological HMC, neural transport HMC, or
  optional contrib integrations should be treated as reference patterns, not as
  required runtime scripts. Optional CUDA, funsor, Horovod, Lightning, Graphviz,
  torchvision, pandas, and scanpy support is unverified in the minimum runtime.

## High-Value Checks Before Answering

1. Confirm the model has continuous latent state for HMC/NUTS; discrete latent
   sites must be observed, enumerated/marginalized correctly, or rerouted.
2. Keep validation on while debugging: use `MCMC(..., disable_validation=False)`
   and fix support/shape errors before tuning sampler parameters.
3. Use constrained values with `init_strategy=init_to_value(...)`; use
   unconstrained tensors only when explicitly passing `initial_params`.
4. Inspect `mcmc.diagnostics()` for `divergences`, `acceptance rate`, `n_eff`,
   and `r_hat`; do not judge convergence from a tiny smoke run.
5. For prediction, decide whether each site should be conditioned from
   `posterior_samples`, sampled anew, or explicitly returned via `return_sites`.
6. For `parallel=True` predictive or multi-chain MCMC, ensure model functions are
   plate-annotated and multiprocessing-safe before blaming Pyro internals.
