# Troubleshooting Contrib And Domain Workflows

Use this reference after routing a Pyro issue to contrib modules, domain example
families, MiniPyro/generic backends, or optional integrations. Keep the first
answer honest about optional dependencies and contrib stability.

## First Triage Checklist

1. **Classify the surface:** `pyro.contrib.*`, `pyro.generic`/MiniPyro,
   `pyro.render_model`, a domain example, or an optional distributed/data/plot
   integration.
2. **Probe optional imports** only in the active user environment; do not assume
   extras are installed from core Pyro import success.
3. **Minimize the run:** small synthetic data, CPU, no plotting, no downloads,
   and few SVI/MCMC steps unless the user requested a full experiment.
4. **Reroute core errors:** if the failing traceback is really about shapes,
   ELBOs, MCMC, enumeration dimensions, or poutine handler order, hand off to
   the corresponding sibling sub-skill after recording domain context.
5. **Warn about stability:** contributed modules have no backwards-compatibility
   guarantee; pin Pyro and smoke-test when upgrading.

## Error And Recovery Matrix

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError: No module named 'funsor'` or `pyro.contrib` lacks `funsor` | Funsor extra absent. `pyro.contrib.__all__` only adds `funsor` if import succeeds. | If ordinary enumeration is enough, use core Pyro `TraceEnum_ELBO` / `infer_discrete`. If named Funsor backend is required, install/provide `pyro-ppl[funsor]` and verify `import pyro.contrib.funsor`. |
| `pyro_backend("contrib.funsor")` not found | `pyro.contrib.funsor` was not imported, or Funsor extra absent. | After installing Funsor, run `import pyro.contrib.funsor` before selecting backend. Otherwise use backend `"pyro"` or `"minipyro"` if appropriate. |
| MiniPyro raises `NotImplementedError` | MiniPyro intentionally implements only a small backend-compatible subset. | Treat as backend limitation. Switch to full `pyro` backend for production features or simplify the didactic example. |
| `DeprecationWarning: pyro.generic has moved to the pyroapi package` | `pyro.generic` is a compatibility shim. | For new backend-agnostic code import from `pyroapi`; keep old `pyro.generic` examples only when adapting versioned Pyro examples. |
| `ImportError` mentioning Graphviz from `pyro.render_model` | Python `graphviz` package absent; file rendering may also need system Graphviz executable. | Install Graphviz only if rendering is required. For debugging, use `poutine.trace(...).get_trace(...).format_shapes()` instead. |
| `ModuleNotFoundError: horovod` or Horovod build/runtime failure | Horovod extra and MPI/build dependencies absent. | Use non-Horovod SVI path for model validation. Ask for Horovod/MPI launcher and install approval for distributed run. |
| `ModuleNotFoundError: lightning` | Lightning extra absent. | Use SVI sub-skill's ELBO module + `torch.optim` pattern without Lightning, or install/provide `pyro-ppl[lightning]`. |
| `ModuleNotFoundError: torchvision`, `pandas`, `scanpy`, `sklearn`, `matplotlib`, `seaborn`, `wget`, or `zuko` | Example/tutorial dependency absent. | Replace with synthetic/mock data if possible. Otherwise ask for targeted install and data/runtime approval. |
| scANVI real PBMC path fails on scanpy/scvi/AnnData | Real single-cell workflow dependencies or schema absent. | Use `dataset="mock"` for smoke/prototype. For real analysis ask for AnnData object/path, label schema, scanpy/scvi environment, and runtime budget. |
| BART forecasting loader downloads or stalls | Full BART data path downloads/cache-preprocesses large ridership data. | Use fake/synthetic data for a smoke model. Ask before network/storage-heavy exact BART reproduction. |
| GP Cholesky fails or returns NaNs | Near-singular kernel matrix, duplicate inputs, too-small noise/jitter, invalid positive parameters. | Increase `jitter`, constrain/noise parameters positive, standardize inputs, reduce model size, inspect kernel matrix condition. Route tensor-shape details to `../distributions-and-shapes/`. |
| Forecasting model raises because `predict` missing or called more than once | `ForecastingModel.model()` contract violated. | Ensure implementation calls `self.predict(noise_dist, prediction)` exactly once. Draw time-dependent noise in `self.time_plate`. |
| Forecast samples have wrong future length | Covariates/data lengths are inconsistent; future covariates must extend beyond observed data. | Check `data.shape[-2]`, `covariates.shape[-2]`, and expected horizon. The fitted forecaster returns samples for covariate times beyond observed length. |
| Forecast/HMM shape error around time dimension | Time axis treated like an ordinary plate or HMM event shape mismatched. | Route to `../distributions-and-shapes/`; keep time as the HMM/event dimension and use `self.time_plate` for time-dependent noise in forecast models. |
| Epidemiology warning about dtype or unstable model | `CompartmentalModel` prefers double precision; particles/quantization/JIT choices may be unstable. | For serious runs set `torch.set_default_dtype(torch.float64)` early, reduce to a tiny synthetic smoke first, then tune SVI/MCMC settings. |
| Epidemiology data generation fails min/max observations | Synthetic SIR generation did not meet requested observed infection count range. | Adjust population, duration, response rate, basic reproduction number, or min/max observation thresholds. Do not treat this as inference failure. |
| Tracking EKF complains about time/frame or covariance | `EKFState` requires `time` or `frame_num`; covariance/state dims inconsistent or not positive-definite. | Supply one time coordinate consistently; verify dynamic model dimension, measurement dimension, and covariance shapes. |
| Capture-recapture or HMM enum dimension error | Discrete latent state enumeration needs correct `max_plate_nesting` and plate dims. | Route to `../effect-handlers-and-enumeration/`; use tiny sequences and explicit plate dims first. |
| Long tutorial appears hung | Defaults can be hundreds/thousands of SVI steps, MCMC samples, epochs, or data downloads. | Stop or ask before continuing. Resume with tiny step counts and no plotting/downloads unless the user approved a full run. |
| CUDA flag fails despite visible GPU host | Active torch build may be CPU-only or tensors are split across devices. | Probe `torch.cuda.is_available()` in the active env; create constants on `data.device`; treat CPU smoke as only partial evidence for CUDA. |
| Contrib API missing after Pyro upgrade | `pyro.contrib` has no backwards-compatibility guarantee. | Pin Pyro to the expected version or update code against the installed docs/API; run a focused import/signature smoke. |

## Optional Import Diagnostic Snippet

Run in the user's active environment when optional dependency state matters:

```python
import importlib.util
names = [
    "pyro", "torch", "pyroapi", "funsor", "graphviz", "horovod", "lightning",
    "torchvision", "pandas", "scanpy", "sklearn", "matplotlib", "seaborn",
    "wget", "zuko",
]
for name in names:
    print(f"{name}: {importlib.util.find_spec(name) is not None}")
```

If an optional package is absent, either skip the optional workflow or ask the
user to install the narrow extra. Do not broaden the environment automatically.

## Missing Funsor Recovery

Use this decision tree:

1. Does the user need the `contrib.funsor` backend, named Funsor dimensions, or
   Funsor-specific TMC? If yes, ask to install/provide Funsor.
2. If the user only needs discrete enumeration in an HMM/mixture/capture model,
   use ordinary Pyro:

   ```python
   from pyro.infer import SVI, TraceEnum_ELBO, config_enumerate
   model = config_enumerate(model, default="parallel")
   svi = SVI(model, guide, optim, TraceEnum_ELBO(max_plate_nesting=...))
   ```

3. If importing `pyro.contrib.funsor` after installation still fails, check the
   pinned compatible Funsor version for this Pyro version and rerun a tiny import
   smoke before debugging model code.

## Missing Graphviz / `pyro.render_model`

`pyro.render_model(...)` is for visualization, not required for inference. If it
fails:

- For structure/shape debugging, use:

  ```python
  from pyro import poutine
  tr = poutine.trace(model).get_trace(*args, **kwargs)
  tr.compute_log_prob()
  print(tr.format_shapes())
  ```

- Install the Python `graphviz` package only if the user needs a graph object.
- Install Graphviz system binaries only if rendering to files requires them in
  the target environment.

## Domain Data And Download Failures

| Domain | Data dependency risk | Safe fallback |
|---|---|---|
| BART forecast | May download/cache/preprocess large ridership files. | Fake/synthetic time-series data and the same `ForecastingModel` structure. |
| scANVI | Real PBMC path needs scanpy/scvi and single-cell data. | `mock` dataset or user-provided tensors. |
| VAE/CVAE/AIR | MNIST/image data, torchvision, plotting, checkpoints. | Synthetic image tensors or tiny local fixture. |
| Mixed HMM | pandas CSV preparation and seal movement schema. | Ask for prepared CSV/schema; use HMM toy data for mechanics. |
| Capture-recapture | Source example has small CSVs, but runtime should not depend on them. | Ask user for capture-history matrix; use tiny binary matrix for prototype. |
| MuE | Biosequence dataset and alphabet assumptions. | Ask for sequences/alphabet; use tiny encoded strings only for smoke. |

When exact tutorial reproduction is requested, clarify network/storage/time and
optional dependency approvals before starting.

## Long Training / Runtime Recovery

Default example settings are often intentionally large:

- forecasting BART: hundreds of steps and many backtest windows;
- epidemiology: many SMC particles, SVI steps, MCMC samples/warmup;
- VAEs/AIR/DMM/scANVI: many epochs and large datasets;
- OED: nested inference inside design grids or Bayesian optimization;
- GP/deep-kernel: O(N^3) kernels or neural feature extraction.

Use this downgrade sequence for a smoke/prototype:

1. CPU only;
2. synthetic/mock/local tiny data;
3. `num_steps`, `num_epochs`, warmup, and samples set to 1-2 where possible;
4. plotting off;
5. downloads off;
6. JIT off until non-JIT works;
7. CUDA/distributed off unless the user specifically asked and environment is
   verified.

State clearly that such a run only verifies wiring, not model quality.

## Contrib Stability / Backcompat Recovery

If code from older docs/examples fails against a new Pyro version:

1. Check the installed `pyro.__version__` and compare with the code's target
   version.
2. Reproduce a minimal import/signature check for the specific contrib module.
3. Look for renamed/moved APIs (for example `pyro.generic` moved to `pyroapi`).
4. Prefer core Pyro primitives/inference APIs when a contrib helper is merely a
   convenience layer.
5. Pin or upgrade deliberately; do not silently mix code from different Pyro
   releases for a scientific result.

## When To Escalate To Sibling Sub-Skills

- Shape, support, event/batch/plate, HMM duration, or GP covariance tensor
  issues: `../distributions-and-shapes/`.
- Model/guide mismatch, ELBO choice, autoguides, optimizer state, minibatching,
  NaN SVI losses: `../svi-and-autoguides/`.
- NUTS/HMC initialization, divergences, predictive sampling, posterior samples:
  `../mcmc-and-prediction/`.
- Enumeration dimensions, `max_plate_nesting`, trace/replay/condition/block,
  poutine masking/scaling/reparameterization: `../effect-handlers-and-enumeration/`.
- Basic primitives, parameter store leakage, `PyroModule`, and top-level
  `pyro.render_model` usage: `../modeling-basics/`.
