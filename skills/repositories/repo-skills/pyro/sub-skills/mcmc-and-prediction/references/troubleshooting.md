# MCMC And Prediction Troubleshooting

Start with validation and tiny runs. Most MCMC failures are model support/shape
issues that become sampler pathologies only after the initial error is ignored.

## MCMC Failure Modes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: Only one of model or potential_fn must be specified` | `NUTS`/`HMC` was constructed with both or neither. | Pass exactly one of `model=` or `potential_fn=`. Prefer `NUTS(model)` for ordinary Pyro programs. |
| `Must provide valid initial parameters ... when using potential_fn` | A custom potential has no model from which Pyro can infer starts. | Provide `initial_params` in the potential function's coordinate system and test finite potential/gradients before sampling. |
| `Model specification seems incorrect - cannot find valid initial params` | Prior samples or default initialization produce invalid support, `-inf` log probability, NaN gradient, or impossible observations. | Enable validation, inspect support constraints, use `init_strategy=init_to_value(...)` or `init_to_feasible()`, and check observed data lie in support. |
| Leading dimension of `initial_params` must match chains | Multi-chain initialization tensors are missing chain dimension or have wrong size. | For `num_chains=k`, each `initial_params[name]` must start with shape `(k, ...)`; for one chain, prefer `init_strategy` unless using `potential_fn`. |
| Invalid support / argument constraint error | A parameter, observation, or initial value violates a distribution support. | Route support details to `../distributions-and-shapes/`; initialize constrained values with `init_to_value`; keep `MCMC(..., disable_validation=False)` while debugging. |
| Invalid `log_prob` shape or stray batch dimensions | Batch dimensions are not declared by `plate` or event dimensions are wrong. | Inspect trace shapes; fix `plate(dim=...)` or `.to_event(...)` in sibling shape guidance before tuning MCMC. |
| `NotImplementedError` about subsample sites | HMC/NUTS model initialization does not support subsampled data plates. | Use full data for MCMC, manually form a smaller fixed dataset for a smoke run, or switch to an SVI/minibatch workflow. |
| Nonzero divergences after warmup | Step size too large for geometry, bad initialization, centered hierarchical funnel, support boundary, or numerically unstable likelihood. | First fix validation/support issues. Then increase `target_accept_prob`, increase warmup, use non-centered/reparameterized model, consider `full_mass` or dense blocks, and inspect potential energy with `hook_fn`. |
| Very low acceptance rate | Large step size, invalid geometry, or starts far from posterior mass. | Increase warmup, raise `target_accept_prob`, improve initialization, lower fixed HMC `step_size`, or reparameterize. |
| Very slow NUTS / tree saturation | Posterior geometry requires deep trees or max tree depth is too low. | Check divergences first. If no support bug, try a higher `max_tree_depth`, better reparameterization, or denser mass matrix; expect higher cost. |
| NaN/Inf during warmup | HMC adaptation can temporarily hit invalid values; persistent NaNs indicate support/numerical bugs. | Keep validation on for development, narrow priors, initialize away from boundaries, clamp only if model semantics justify it, and check all likelihood scales/rates are finite and positive. |
| `r_hat` high or `n_eff` low | Chains are not mixing, too few samples, multimodality, or poor parameterization. | Run more warmup/samples/chains, inspect chain-specific samples with `group_by_chain=True`, reparameterize, or use domain constraints/priors. |
| `num_chains` warning about available CPU | Requested more parallel chains than worker capacity. | Reduce `num_chains` or accept sequential chain drawing. Do not treat sequential fallback as failed inference. |
| Multiprocessing pickling or spawn errors | Model/kernel closure, lambda, local class, notebook state, or CUDA context is not serializable. | Use top-level functions/classes, avoid unpicklable closures, set `num_chains=1` while debugging, and use `mp_context="spawn"` for CUDA tensors. |
| Progress bars pollute logs or hang non-interactive output | Default progress display is enabled. | Set `disable_progbar=True`; use `hook_fn` or logging for structured diagnostics. |
| JIT warnings or wrong JIT result | Dynamic control flow/site structure or tensor-dependent Python behavior under `jit_compile=True`. | Debug non-JIT first. Use JIT only for static models, pass stable tensor inputs, and set `ignore_jit_warnings=True` only after comparing results. |
| Memory blow-up from retained samples | Too many chains/samples or large latent sites retained. | Reduce retained samples, use `save_params=[...]`, stream summaries with `StreamingMCMC` for advanced memory-constrained runs, or move bulky deterministic prediction out of MCMC samples. |

## Discrete Latent Variables

HMC/NUTS cannot directly move in a discrete latent state. If a model has latent
`Categorical`, `Bernoulli`, integer count, or other enumerable sites:

1. Verify whether each discrete site is observed. Observed sites are fine.
2. If unobserved and finite, decide whether exact enumeration/marginalization is
   intended. Set `max_plate_nesting` when needed and route enumeration mechanics
   to `../effect-handlers-and-enumeration/`.
3. If enumeration is infeasible, use SVI with enumeration/autoguides,
   reparameterize, use `infer_discrete` for posterior decoding after continuous
   inference, or choose another algorithm.
4. Do not create floating-point `initial_params` for a genuinely discrete site;
   that hides the modeling problem rather than making HMC valid.

A typical failing pattern is a mixture assignment sampled under a data plate with
no enumeration/shape plan. Fix by marginalizing assignments, using
`config_enumerate` with correct plate nesting, or rerouting to an SVI/enumeration
workflow.

## Predictive Failure Modes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Either posterior_samples or num_samples must be specified` | Prior predictive call omitted `num_samples`. | Use `Predictive(model, num_samples=N, ...)` when no posterior samples are supplied. |
| Warning that posterior sample leading dimension differs from `num_samples` | `posterior_samples` batch size and requested `num_samples` disagree. | Omit `num_samples` or resample/slice posterior tensors yourself before constructing `Predictive`. |
| Missing deterministic or observed site in output | Default `return_sites=()` did not include what you expected, or the site was conditioned. | Pass explicit `return_sites=[...]`; include deterministic names and observed site names such as `"obs"`. |
| Predictive returns observed training data instead of new observations | The model call still passed non-`None` `obs`. | Make observation arguments optional and call predictive with `obs=None` or equivalent. |
| Shape has unexpected singleton dimensions | Plate/event semantics or `parallel=True` vectorization introduced broadcast dimensions. | Print all returned shapes; avoid blind `squeeze`; repair model plate/event declarations in the shape sibling skill. |
| `parallel=True` predictive fails but sequential works | Model/guide lacks complete `plate` annotation or has dynamic batch structure. | Use `parallel=False` or repair plates so every batch dimension is declared. |
| `posterior_samples` plus `guide` raises an error | Pyro forbids providing both to `Predictive`. | Use either MCMC/explicit posterior samples or a guide-based predictive call, not both. |
| Weighted predictive has low ESS or unstable weighted quantiles | Guide poorly matches the target conditioned model. | Improve/refit guide in `../svi-and-autoguides/`, increase samples, inspect `log_weights`, or use `MHResampler` for repeated resampling. |
| `get_vectorized_trace()` fails | Model is not valid under vectorized predictive plate. | Use ordinary `Predictive(...)(...)` first; only request vectorized traces for static, plate-annotated models. |

## Optional Backend And Dependency Notes

The minimum verified runtime covers CPU Pyro package use. Treat these as optional
unless the active environment proves otherwise:

- CUDA tensors and multi-chain CUDA multiprocessing;
- funsor-backed enumeration examples;
- Horovod or Lightning integrations;
- Graphviz/model rendering;
- torchvision, pandas, scanpy, plotting, or tutorial data dependencies.

Do not prescribe installing broad extras merely to fix a core NUTS or Predictive
shape/support issue.
