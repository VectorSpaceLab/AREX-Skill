# ZhuSuan workflows and example families

This repo is best understood as a set of probabilistic-modeling workflows.
Use this page to choose the right sub-skill and to see which examples require
external data or optional helpers.

## Workflow families

| Workflow family | Main files | Typical inputs | Notes | Best sub-skill |
| --- | --- | --- | --- | --- |
| Core probabilistic modeling | `docs/tutorials/concepts.rst`, `zhusuan/framework/*`, `zhusuan/distributions/*` | TensorFlow tensors and observations | Build Bayesian graphs, inspect nodes, and define custom joint scores | `modeling-primitives` |
| Variational inference | `docs/tutorials/vae.rst`, `docs/tutorials/bnn.rst`, `examples/variational_autoencoders/*`, `examples/bayesian_neural_nets/*` | MNIST, UCI data, variational posteriors, particles | ELBO, IWAE, REINFORCE, VIMCO, and importance-sampling evaluation | `variational-inference` |
| Normalizing flows | `zhusuan/transform.py`, `examples/normalizing_flows/vae_nf.py` | latent samples and log-probabilities | Planar flows and inverse autoregressive flows on the variational path | `variational-inference` |
| GP variational models | `examples/gaussian_process/svgp.py`, `examples/gaussian_process/utils.py` | external regression data and inducing points | Sparse variational GP helper path | `variational-inference` |
| HMC / SG-MCMC | `zhusuan/hmc.py`, `zhusuan/sgmcmc.py`, `examples/toy_examples/*` | log joints, latent variables, minibatches | Exact-ish sampling, stochastic-gradient sampling, and toy posterior checks | `mcmc-and-sampling` |
| AIS / diagnostics | `zhusuan/evaluation.py`, `zhusuan/diagnostics.py`, `examples/topic_models/lntm_mcem.py` | proposal model, target model, chains | Annealed importance sampling and effective sample size | `mcmc-and-sampling` |

## Example families and data notes

- Toy examples are self-contained and can be used as light reference runs.
- VAE / IWAE / flow examples usually need MNIST caches or download access.
- BNN examples use UCI-style regression data and minibatching.
- PMF and topic-model examples depend on external dataset files and can be
  slow.
- GAN examples rely on optional image-grid helpers and are outside the minimum
  verification set.

## Safe bundled helpers

- `scripts/data_helpers.py` for normalization and one-hot conversion
- `scripts/image_grid.py` for optional image output
- `scripts/core_smoke.py` for a tiny import/objective check
- `sub-skills/variational-inference/scripts/gp_helpers.py` for the SVGP helper
  path
