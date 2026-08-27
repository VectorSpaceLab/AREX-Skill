# Advanced contrib troubleshooting

Use this file when optional NumPyro contrib workflows fail. Most failures are dependency, shape, or side-effect issues rather than core NumPyro bugs.

## Quick triage

1. Run `python scripts/check_optional_dependencies.py --pretty` from this sub-skill directory.
2. If a specific capability is required, run `python scripts/check_optional_dependencies.py --require <checker-key> --pretty`.
3. Keep a tiny synthetic smoke test separate from any long example, dataset loader, plot, or benchmark.
4. Reroute core-only issues to the sibling sub-skills instead of debugging them here.

## Missing optional dependencies

| Symptom | Likely cause | Fix or route |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'funsor'` | Funsor is not installed | Install/verify `funsor`; require `funsor` with the checker. If installation is impossible, use non-enumerated alternatives and explain the change. |
| `ImportError` from `numpyro.contrib.nested_sampling` mentioning `jaxns` | `jaxns` is missing | Require `nested_sampling`; install/verify `jaxns` first, then verify TFP. Do not claim `NestedSampler` is part of a minimal NumPyro install. |
| `ModuleNotFoundError: No module named 'tensorflow_probability'` | TFP JAX substrate is missing | Install/verify a TFP package compatible with installed JAX. Needed for TFP distributions/MCMC, nested sampling import, and HSGP periodic/RQ Bessel functions. |
| Flax wrapper import error | `flax` is missing | Require `module_flax`; install/verify Flax. Preserve `flax_module`/`random_flax_module` parameter semantics instead of rewriting the model silently. |
| NNX wrapper import error or missing `flax.nnx` | Installed Flax is absent or too old for NNX | Require `module_nnx`; install/verify a recent Flax with NNX. Pre-initialize NNX modules outside the NumPyro model. |
| Equinox wrapper import error | `equinox` is missing | Require `module_equinox`; install/verify Equinox. Pre-initialize Equinox modules outside the model and use `jax.vmap` for batched calls. |
| Missing `optax`, `matplotlib`, `pandas`, `sklearn`, or `graphviz` | Example-only optimizer, plotting, data, or rendering dependency is missing | Do not treat this as a missing core contrib API. Install only if the user asks for that example-side behavior. |

## Funsor enumeration issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Shape/broadcast errors after marking sites with `infer={"enumerate": "parallel"}` | Enumerated dimensions collide with plate/batch dimensions | Set `first_available_dim` explicitly; test a very short model; keep plate dims explicit. |
| Wrong indexing into parameters by an enumerated discrete value | Ordinary indexing does not preserve enum dimensions | Use vectorized enum-aware indexing such as `Vindex` patterns. |
| `infer_discrete` returns deterministic MAP when posterior samples were expected | `temperature=0` | Use `temperature=1` and provide `rng_key` for posterior sampling. |
| Slow or confusing Markov enumeration | Long `markov`/`scan` chain | Test a short sequence first; avoid scaling until enum dimensions and observations are correct. |

## HSGP issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Poor approximation near input extremes | Inputs are too close to `[-ell, ell]` boundaries | Center/scale inputs and choose `ell` comfortably larger than the observed range. |
| Large memory/compile time in multi-dimensional HSGP | Basis count is `prod(m)` | Reduce per-dimension `m`, start with 1D or additive components, and increase gradually. |
| `ell must be a scalar or a list of length dim` | `ell` shape does not match inferred input dimension | If `x.shape[-1] == D`, pass scalar `ell` or a length-`D` list/array shaped as expected. |
| Periodic kernel rejects multidimensional input | `hsgp_periodic_non_centered` is univariate | Model periodic components one dimension at a time or choose a non-periodic HSGP function. |
| Rational-quadratic spectral density fails or diverges | TFP missing, non-isotropic length, or `scale_mixture <= dim/2` | Verify `hsgp_tfp`; use scalar length for multi-dimensional RQ; choose `scale_mixture > dim/2`. |

## Nested sampling issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing `jaxns` import | Optional `jaxns` dependency absent | Verify with `--require nested_sampling`; install/verify `jaxns` and TFP if allowed. |
| Numeric instability or poor nested-sampling behavior | Double precision disabled or run too small | Call `numpyro.enable_x64()` for real runs; tune `num_live_points`, `max_samples`, and `dlogZ`. |
| Failure from inverse CDF during uniform reparameterization | Prior distribution lacks supported inverse-CDF path | Switch prior/reparameterization where possible or use a core MCMC method. |
| Plots appear or plotting fails | `diagnostics()` creates plotting side effects | Do not call diagnostics in no-plot/headless contexts unless the user asked for plots and dependencies are available. |

## Neural module wrapper issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `flax_module` cannot initialize parameters | No `input_shape`, positional init args, or keyword init args were provided | Supply `input_shape`, dummy positional inputs, or keyword inputs so Linen can run `init`. |
| Flax dropout behaves deterministically or fails on RNGs | `apply_rng`/runtime `rngs` mismatch | Pass `apply_rng=["dropout"]` to `flax_module` and call the returned net with `rngs={"dropout": numpyro.prng_key()}`. |
| BatchNorm or stateful modules do not update state | Mutable state was not declared or carried | For Flax Linen pass `mutable=["batch_stats"]`; for NNX/Equinox use NumPyro mutable state holders as appropriate. |
| Random module wrapper samples do not include expected parameter names | Prior dictionary keys do not match flattened parameter paths | Inspect the framework's parameter tree in a tiny trace and adjust keys such as `kernel`, `bias`, `inner.dense.kernel`, `layers.0.bias`, or Equinox key paths. |
| Batched Equinox module shape errors | Equinox modules are called on one example but data are batched | Wrap the Equinox module with `jax.vmap` for batched inputs. |

### Difficult Flax wrapper failure case

Symptom: a user asks to wrap a Flax model and `flax_module` or `random_flax_module` fails because Flax is missing.

Response pattern:

1. Explain that Flax integration is optional.
2. Verify with `python scripts/check_optional_dependencies.py --require module_flax --pretty`.
3. If installation is allowed, install/verify Flax, then test a tiny trace with `input_shape` before inference.
4. Preserve parameter handling: deterministic wrappers register `name$params`; random wrappers sample prior-covered leaves under scoped sample-site names.
5. If installation is not allowed, ask whether to replace the neural network with a native JAX function or defer the Flax-specific task.

## Stochastic-support issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Runtime error says branching is only supported for discrete sampling sites | A branch site is continuous or lacks discrete support | Only annotate discrete sites with `infer={"branching": True}`. |
| Run time explodes | Too many discovered straight-line programs | Lower `num_slp_samples`, lower `max_slps`, simplify branches, or use a different inference strategy. |
| `SDVI` rejects the loss | Loss is not one of the supported ELBO classes | Use `Trace_ELBO`, `TraceMeanField_ELBO`, `TraceEnum_ELBO`, or `TraceGraph_ELBO`. |

## Backend, dataset, and side-effect issues

- Set CPU explicitly for safe smoke tests when GPU/TPU availability is uncertain.
- Do not run long examples, benchmarks, or dataset loaders unless the user explicitly requested them and the budget allows it.
- Examples may download datasets, open plots, save PDFs, or require scikit-learn/pandas/matplotlib. Replace them with tiny synthetic data for API checks.
- If a task asks for rendering or diagnostics plots, verify plotting/rendering dependencies and decide the output file policy before running code.
