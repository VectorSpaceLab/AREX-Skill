# MCMC and sampling workflows in ZhuSuan

## 1. HMC

`zs.HMC(...)` is the main exact-ish sampler in ZhuSuan.

Typical pattern:

1. Build a `log_joint` function or use a `MetaBayesianNet`.
2. Create `Variable` objects for the latent state.
3. Call `hmc.sample(meta_bn, observed, latent)` once.
4. Run the returned `sample_op` in a loop.

Important knobs:

- `step_size`
- `n_leapfrogs`
- `adapt_step_size`
- `target_acceptance_rate`
- `adapt_mass`

Adaptation should usually be confined to burn-in. The example code does this by
feeding placeholder flags.

## 2. SG-MCMC

Use stochastic-gradient MCMC when the log joint is estimated from minibatches.
The subclasses are:

- `SGLD`
- `PSGLD`
- `SGHMC`
- `SGNHT`

SGHMC and SGNHT expose momentum / friction diagnostics through the returned
`sgmcmc_info` tuple.

## 3. AIS

`zs.evaluation.AIS` combines a proposal `MetaBayesianNet`, a target model, and
an `HMC` sampler across a temperature schedule.

Workflow summary:

- initialize latent variables from the proposal
- adapt the HMC step size briefly
- anneal from the proposal to the target
- aggregate the log weights into a lower-bound estimate

## 4. Example families and data dependencies

- `examples/toy_examples/gaussian.py`: tiny Gaussian HMC demo
- `examples/toy_examples/mixture_sgnht.py`: SGNHT toy posterior
- `examples/probabilistic_matrix_factorization/pmf_hmc.py`: large HMC PMF run
- `examples/topic_models/lntm_mcem.py`: topic model with AIS/HMC

The last two examples depend on external data files and long-running loops, so
use them as reference workflows unless the user explicitly asks for a full run.
