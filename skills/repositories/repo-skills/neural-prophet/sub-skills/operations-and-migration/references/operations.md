# NeuralProphet operations guide

This guide is for operating an installed NeuralProphet runtime. It assumes the Python distribution is `neuralprophet`, the import package is `neuralprophet`, and the generated skill targets version `1.0.0rc10` behavior.

## 1. Installation and version checks

### CLI check

NeuralProphet exposes a minimal module CLI. It is useful for version checks only:

```bash
python -m neuralprophet --version
python -m neuralprophet -V
```

Expected behavior: the command exits with status 0 and prints a line containing the installed NeuralProphet version. There are no training or forecasting subcommands in the CLI.

### Python import check

Use this when diagnosing an environment before running heavier fits:

```python
from importlib import metadata
import neuralprophet
from neuralprophet import NeuralProphet, TorchProphet, load, save, set_log_level, set_random_seed

print("neuralprophet distribution:", metadata.version("neuralprophet"))
print("neuralprophet module:", neuralprophet.__version__)
print("NeuralProphet class:", NeuralProphet)
print("TorchProphet class:", TorchProphet)
```

If this import fails before your own code runs, first check the compatibility notes in [troubleshooting.md](troubleshooting.md), especially the `pandas<3` and `setuptools<81` surfaces.

### Optional plotting extras

Base plotting can use `matplotlib` and `plotly` when those dependencies are present. Additional behavior may require extras:

- `plotly-resampler` is optional. If the backend is set to `plotly-resampler` without the package, NeuralProphet may log a misleading message that says Plotly import failed even though the missing import is the resampler.
- `plotly-static` requires static export support through Kaleido. If static SVG export fails, use `plotly` or `matplotlib` until Kaleido is repaired.
- README-style install guidance includes a live-loss option for notebook use. For ordinary non-interactive operation, do not require notebook/live plotting extras.

## 2. Logging and reproducibility

NeuralProphet registers loggers under the `NP` namespace and reduces PyTorch Lightning logs at import time. Control logs with the public helper:

```python
from neuralprophet import set_log_level

set_log_level("ERROR", include_handlers=True)   # quiet operational smoke tests
set_log_level("INFO")                           # restore normal status messages
```

Valid log levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL` or their numeric logging values. `include_handlers=True` also updates attached stream/file handlers.

For repeatable experiments, seed immediately before each fit:

```python
from neuralprophet import set_random_seed

set_random_seed(42)
metrics = model.fit(df, freq="D", deterministic=True, minimal=True)
```

`set_random_seed(seed)` seeds NumPy, Torch, and Lightning worker seeding. `fit(..., deterministic=True)` asks the Lightning trainer to use deterministic operations where possible. Exact reproducibility can still vary across hardware, Torch kernels, dependency versions, and accelerator backends.

## 3. CPU, accelerator, and trainer configuration

NeuralProphet does not require CUDA by default. For small operational tests, use CPU and disable noisy side effects:

```python
from neuralprophet import NeuralProphet

model = NeuralProphet(
    epochs=2,
    batch_size=16,
    learning_rate=0.1,
    collect_metrics=False,
    accelerator="cpu",
)
metrics = model.fit(
    df,
    freq="D",
    minimal=True,
    progress=None,
    checkpointing=False,
    trainer_config={"default_root_dir": runtime_temp_dir},
)
```

Operational rules:

- `accelerator=None` leaves accelerator selection deactivated; `accelerator="cpu"` forces CPU; `accelerator="auto"` attempts to use available GPU/MPS accelerators and falls back to CPU when none are available.
- `trainer_config` is passed through to the PyTorch Lightning `Trainer`. Use it for caller-managed trainer options such as `default_root_dir`, callbacks, precision, device counts, and logger behavior.
- `fit(..., checkpointing=False)` avoids checkpoint artifacts. If you provide a `ModelCheckpoint` callback, enable checkpointing or remove the callback.
- `fit(..., minimal=True)` disables metrics, progress plotting, and checkpointing in one switch. This is appropriate for smoke tests, not for full model evaluation.
- Do not assume GPU availability in reusable scripts. Prefer CPU defaults and make accelerator use an explicit caller decision.

## 4. Save and load workflow

Use the package-level helpers, not raw `torch.save` in user code:

```python
from neuralprophet import NeuralProphet, save, load

model = NeuralProphet(epochs=2, batch_size=16, learning_rate=0.1, collect_metrics=False, accelerator="cpu")
model.fit(df, freq="D", progress="bar", checkpointing=False)
future = model.make_future_dataframe(df, periods=3)
forecast_before = model.predict(future)

save(model, model_path)                 # path-like object or binary buffer; .np extension is conventional
loaded = load(model_path, map_location="cpu")
forecast_after = loaded.predict(future)
```

Important behavior:

- `save(forecaster, path)` temporarily removes trainer references from the forecaster and model, calls Torch serialization, then restores the removed attributes on the in-memory object.
- `load(path, map_location=None)` loads a previously saved model and restores a trainer. Use `map_location="cpu"` when loading on a CPU-only machine or when moving a saved GPU model to CPU.
- The helpers accept path-like objects and in-memory binary buffers.
- Serialized NeuralProphet models are Torch/Pickle artifacts. Load only trusted files produced by compatible package versions.
- After loading, validate by predicting on a known future dataframe and checking that at least one `yhat*` column is present.
- In this version, a model fitted with progress disabled can persist a Lightning `enable_progress_bar=False` flag that conflicts with trainer restoration during load. If this appears, either fit with the default progress-bar setting before saving or remove the stale flag from the stored trainer configuration before calling `save`.

A self-contained smoke test is bundled at `scripts/save_load_smoke.py` and includes the no-progress restore safeguard.

## 5. Plotting backend operations

NeuralProphet plot methods accept a per-call `plotting_backend` argument and also support setting a model default:

```python
model.set_plotting_backend("matplotlib")
fig = model.plot(forecast)

fig = model.plot(forecast, plotting_backend="plotly")
fig = model.plot_components(forecast, plotting_backend="plotly")
fig = model.plot_parameters(plotting_backend="matplotlib")
```

Supported backend values:

| Backend | Use when | Notes |
| --- | --- | --- |
| `matplotlib` | Need non-interactive, broad compatibility | Returns Matplotlib figure/axes style objects. Close figures in long-running scripts. |
| `plotly` | Need interactive Plotly figures | Requires Plotly import support. |
| `plotly-static` | Need static SVG export from Plotly | Requires Kaleido static export support. |
| `plotly-resampler` | Need large interactive Plotly figures in supported notebooks | Optional extra; unsupported environments may auto-switch or warn. |

Operational checks after plotting:

- Confirm the returned figure object is not `None`.
- For static exports, verify an image or SVG was actually emitted by the plotting backend.
- If `plotly-resampler` logs errors, retry with `plotly` before treating Plotly itself as broken.
- Route conformal prediction and uncertainty-specific plots to `../evaluation-and-uncertainty/`.

## 6. TorchProphet migration workflow

`TorchProphet` is a compatibility wrapper that lets some Prophet-style code run on NeuralProphet. It is best used as a migration bridge, not as a guarantee of full Prophet parity.

```python
from neuralprophet import TorchProphet as Prophet

m = Prophet(
    growth="linear",
    yearly_seasonality="auto",
    weekly_seasonality="auto",
    daily_seasonality="auto",
    seasonality_mode="additive",
    interval_width=0.8,
    epochs=2,
    batch_size=32,
    learning_rate=0.1,
)
metrics = m.fit(df)
future = m.make_future_dataframe(periods=14, freq="D", include_history=True)
forecast = m.predict(future)
```

Migration checklist:

1. Keep Prophet-style input columns `ds` and `y`; remove logistic `cap` columns because saturating forecasts are not supported by the wrapper.
2. Map `growth="flat"` to NeuralProphet `growth="off"` behavior. The wrapper logs this conversion.
3. Treat `interval_width` as a way to create symmetric NeuralProphet quantiles unless `quantiles` is passed directly.
4. Convert Prophet prior scales to NeuralProphet regularization knobs instead of passing `_prior_scale` arguments.
5. Use `add_regressor(name, standardize="auto")` for Prophet-style future regressors, but prefer `NeuralProphet.add_future_regressor(...)` when you need explicit additive/multiplicative mode control.
6. Use `add_seasonality(name, period, fourier_order, mode=...)`; do not rely on Prophet conditional seasonalities through `condition_name` in the wrapper.
7. Expect warnings for Prophet-only concepts such as Stan backend, MCMC samples, uncertainty samples, plot capacity, and some plot legend/focus controls.

For component-heavy native NeuralProphet code, prefer direct `NeuralProphet` APIs and route detailed component modeling to `../components-and-exogenous/`.

## Self-contained use

This runtime guide distills the operational behavior needed for package use; do not depend on upstream source files, notebooks, tests, or maintainer scripts while using it.
