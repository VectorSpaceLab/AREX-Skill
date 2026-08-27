# Optional dependency matrix

Core NumPyro depends on JAX/JAXLIB, NumPy, `multipledispatch`, and `tqdm`. The published package extras in this checkout are backend-oriented (`cpu`, `cuda12`, `cuda13`, `tpu`); they do not install every contrib dependency. Most contrib features below require separate optional packages.

Use the bundled checker before relying on a capability:

```bash
python scripts/check_optional_dependencies.py --pretty
python scripts/check_optional_dependencies.py --require funsor
python scripts/check_optional_dependencies.py --require nested_sampling module_flax
```

If `--require` is omitted, missing optional packages are reported in JSON but do not make the script fail.

## Matrix

| Checker key | Imports probed | Needed for | Install hint | Common missing symptom |
| --- | --- | --- | --- | --- |
| `core` | `numpyro`, `jax` | Any NumPyro task | Install NumPyro with the appropriate JAX backend extra for the target hardware | Core import failure; do not debug contrib until this is fixed |
| `funsor` | `funsor`, `numpyro.contrib.funsor` | `config_enumerate`, `infer_discrete`, `markov`, enumerated SVI/log-density helpers | Install `funsor>=0.4.1` | `ModuleNotFoundError: No module named 'funsor'` |
| `hsgp` | `numpyro.contrib.hsgp.approximation`, `numpyro.contrib.hsgp.spectral_densities` | HSGP squared-exponential and Matérn approximations plus base helper imports | No extra package for basic imports beyond core NumPyro | Shape/domain errors are usually modeling choices, not missing deps |
| `hsgp_tfp` | `tensorflow_probability.substrates.jax` | HSGP periodic and rational-quadratic Bessel functions | Install a TensorFlow Probability package compatible with the installed JAX version | `TensorFlow Probability is required for this function` or for rational-quadratic spectral density |
| `nested_sampling` | `jaxns`, `tensorflow_probability.substrates.jax`, `numpyro.contrib.nested_sampling` | `NestedSampler`, `UniformReparam`, evidence-style nested sampling | Install `jaxns` in the version range compatible with NumPyro and install a compatible TFP JAX substrate | Import error mentioning `jaxns`; after that, possible TFP import error |
| `einstein` | `numpyro.contrib.einstein` | `SteinVI`, `SVGD`, `ASVGD`, Stein kernels, `MixtureGuidePredictive` | Usually core NumPyro is enough for imports; examples may need more packages | Missing example dependencies should not be interpreted as missing SteinVI |
| `module_flax` | `flax`, `numpyro.contrib.module` | `flax_module`, `random_flax_module` for Flax Linen modules | Install `flax`; for stochastic layers verify compatible JAX/Flax versions | Import error message says Flax must be installed to declare NN modules |
| `module_nnx` | `flax`, `flax.nnx`, `numpyro.contrib.module` | `nnx_module`, `random_nnx_module` | Install a recent Flax that includes NNX | `ImportError` or missing `flax.nnx` when using NNX wrappers |
| `module_equinox` | `equinox`, `numpyro.contrib.module` | `eqx_module`, `random_eqx_module` | Install `equinox` compatible with the installed JAX version | Import error message says Equinox must be installed |
| `tfp` | `tensorflow_probability.substrates.jax`, `numpyro.contrib.tfp.distributions`, `numpyro.contrib.tfp.mcmc` | TFP JAX distributions in NumPyro, TFP bijectors, TFP transition kernels | Install a TFP package compatible with the installed JAX version; use direct substrate imports when possible | `ModuleNotFoundError: No module named 'tensorflow_probability'` or TFP/JAX version errors |
| `stochastic_support` | `numpyro.contrib.stochastic_support.dcc`, `numpyro.contrib.stochastic_support.sdvi` | `DCC`, `SDVI`, branch-conditioned straight-line program inference | No extra package for imports beyond core NumPyro | Runtime errors usually come from continuous branch sites or too many SLPs |
| `optax` | `optax` | Optional optimizers used in some examples; NumPyro can also use `numpyro.optim` | Install `optax` if the task asks for an Optax optimizer | `ModuleNotFoundError: No module named 'optax'` |
| `example_plotting_data` | `matplotlib`, `pandas`, `sklearn` | Plotting, tabular data loading, and example-only preprocessing | Install only when needed by a user-visible plotting/data task | Missing imports in examples; not required for core contrib APIs |
| `rendering` | `graphviz` | Rendering/model graph side effects | Install only for explicit rendering tasks | Graph rendering import failure |

## Verification hints

- To verify nested sampling specifically:
  ```bash
  python scripts/check_optional_dependencies.py --require nested_sampling --pretty
  ```
  If this fails on `jaxns`, install/verify `jaxns` first. If it then fails on TFP, verify `tensorflow_probability.substrates.jax` separately.

- To verify Flax module wrappers:
  ```bash
  python scripts/check_optional_dependencies.py --require module_flax --pretty
  ```
  Then run a tiny trace with `flax_module(..., input_shape=...)` before SVI or MCMC.

- To verify Funsor enumeration:
  ```bash
  python scripts/check_optional_dependencies.py --require funsor --pretty
  ```
  Then run a short enumerated model before scaling to long Markov sequences.

- To verify HSGP periodic or rational-quadratic code, require both `hsgp` and `hsgp_tfp`.

## Interpreting optional import failures

- Missing optional packages should be surfaced to the user as dependency caveats, not hidden by silently replacing the requested algorithm.
- If the user cannot install optional packages, reroute to the closest core workflow and explain the loss of capability: e.g. NUTS/DiscreteHMCGibbs instead of `NestedSampler`, native NumPyro distributions instead of TFP distributions, or core SVI instead of SteinVI only if SteinVI itself is not required.
- Example-only packages (`matplotlib`, `pandas`, `sklearn`, `graphviz`, `optax`) are not proof that an API is unavailable. They often appear because examples load datasets, plot figures, or use nonessential optimizer variants.
