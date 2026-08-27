# Operations troubleshooting

Use this when NeuralProphet fails before or around operational tasks: import/version checks, CLI checks, logging, plotting backend selection, save/load, accelerator selection, or TorchProphet migration.

## Quick triage order

1. Run `python -m neuralprophet --version` to separate package import failures from task code failures.
2. Import the public APIs: `NeuralProphet`, `TorchProphet`, `save`, `load`, `set_log_level`, and `set_random_seed`.
3. If import fails, check dependency compatibility before changing forecasting code.
4. If import succeeds, reproduce with a tiny CPU fit and `scripts/save_load_smoke.py`.
5. For plotting failures, retry with `plotting_backend="matplotlib"` or `"plotly"` before debugging optional resampler/static export paths.

## Compatibility failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import or fit fails with a message involving `Series.view`, `pandas.Series.view`, or a removed pandas view operation. | This NeuralProphet version uses pandas behavior removed in pandas 3. | Use `pandas<3` for this NeuralProphet runtime. Re-run the import check and a tiny CPU fit after changing the environment. |
| Import or Lightning setup fails with a missing `pkg_resources` error. | `lightning-fabric` or `pytorch-lightning` in this dependency set may still rely on `pkg_resources`, which is removed from newer setuptools releases. | Use `setuptools<81` with this runtime, then re-run `python -m neuralprophet --version`. |
| Version command works but training fails during automatic learning-rate selection. | `learning_rate=None` can trigger extra Lightning/Torch machinery. | For operational checks, set a small explicit `learning_rate`, `epochs`, and `batch_size`. Leave tuning decisions to forecasting workflows. |
| `n_forecasts` is changed to 1 during fit. | NeuralProphet cannot produce independent multi-step forecasts with `n_lags=0`. | Use `n_lags>0` for direct multi-step forecasting, or accept one-step forecasts. Route modeling design to `../core-forecasting/`. |

## Plotting failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Log says `Importing plotly failed. Interactive plots will not work.` even though Plotly appears installed. | In the plotting modules, the same error can be emitted when optional `plotly-resampler` import fails. | If the task does not need resampling, use `plotting_backend="plotly"` or `"matplotlib"`. If resampling is required, install or repair the optional `plotly-resampler` package. |
| `plotly-resampler is not installed. Please install it to use the resampler.` | Backend requested `plotly-resampler`, but the optional package is absent. | Retry with `plotting_backend="plotly"`; install the optional resampler only when large interactive notebook plots are required. |
| Plotly static/SVG export fails. | `plotly-static` requires Kaleido static export support. | Use `plotting_backend="plotly"` for interactive figures or `"matplotlib"` for static non-interactive checks until Kaleido is available. |
| Resampler warns that the current environment is unsupported or auto-switches. | `plotly-resampler` is designed for supported notebook environments and may not work in ordinary terminals or some IDEs. | Use `plotly` or `matplotlib` for scripts and CI-like checks. |
| Plot method returns `None` or no visible window in a headless run. | Interactive display is unavailable. | Treat figure object creation as the validation target; save/export only when the backend supports it. Close Matplotlib figures in long-running processes. |
| Uncertainty or conformal plot interpretation is unclear. | This sub-skill covers backend operation, not uncertainty semantics. | Route to `../evaluation-and-uncertainty/`. |

## Save/load and serialization failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Loading a saved GPU model fails on a CPU-only machine. | Torch storage is mapped to the original accelerator by default. | Load with `load(model_path, map_location="cpu")`. Validate by predicting and checking `yhat*` columns. |
| Save creates or references trainer state unexpectedly. | Raw Torch serialization includes object state; NeuralProphet's `save` helper removes trainer references before writing. | Use `from neuralprophet import save, load` rather than calling raw `torch.save` from task code. |
| Save overwrites an existing user file. | The caller supplied an existing output path. | Do not overwrite unless the user explicitly requested it. Use a temporary file for smoke tests. |
| Load fails with Torch/Pickle safety or class resolution errors. | Serialized models are Python object artifacts and require trusted compatible package versions. Newer Torch safety defaults can also reject object pickles. | Load only trusted files; use matching NeuralProphet/Torch dependency versions when possible; for operational checks regenerate a fresh model with the bundled smoke script. |
| Loading after a no-progress or `minimal=True` fit fails with `enable_progress_bar=False` and `ProgressBar` in callbacks. | The saved Lightning trainer configuration retained a stale no-progress flag; trainer restoration adds NeuralProphet's progress-bar callback. | Fit with the default progress setting before saving, or remove the stale `enable_progress_bar` key from the stored trainer configuration before `save`. The bundled smoke script applies this safeguard. |
| Predictions after load do not contain `yhat*` columns. | Wrong dataframe passed to `predict`, incompatible model/data state, or load did not restore a fitted forecaster. | Rebuild the future dataframe from the same history and required exogenous frames, then retry. If the model was never fitted, train before saving. |

## Accelerator and trainer failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA device error, no GPU visible, or accelerator not available. | Code assumed CUDA/GPU availability. | For operational checks, instantiate with `accelerator="cpu"` or leave accelerator unset; load with `map_location="cpu"`. Do not require CUDA by default. |
| MPS/GPU auto-selection is slow or unstable. | `accelerator="auto"` can pick a backend that is present but unsuitable for the task. | Force `accelerator="cpu"` for reproducibility and minimal validation; use explicit GPU/MPS settings only when the user requested accelerator execution. |
| Lightning writes unwanted logs or checkpoints. | Trainer defaults and checkpoint settings can create artifacts. | Use `fit(..., minimal=True, progress=None, checkpointing=False)` and supply a caller-managed temporary `default_root_dir` through `trainer_config`. |
| Trainer callback error says checkpointing is disabled but a `ModelCheckpoint` callback is provided. | Custom `trainer_config` included a checkpoint callback while `checkpointing=False`. | Enable checkpointing for that run or remove the checkpoint callback. |
| Re-fitting a loaded or already fitted model raises `RuntimeError: Model has been fitted already.` | NeuralProphet prevents fitting the same forecaster twice in ordinary `fit`. | Create a new model for a new training run. Use loaded models primarily for prediction unless a documented continue-training workflow is explicitly being used. |

## Logging and reproducibility issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| NeuralProphet emits too much status output. | `NP` loggers and progress bars are active. | Call `set_log_level("ERROR", include_handlers=True)` and use `fit(..., progress=None, minimal=True)` for smoke scripts. |
| Log level call appears to do nothing for attached handlers. | Handler levels were not updated. | Use `include_handlers=True` in `set_log_level`. |
| Runs differ despite setting a seed. | Seed was set too early or nondeterministic kernels/backends are in use. | Call `set_random_seed(seed)` immediately before each `fit`, use `fit(..., deterministic=True)`, and force CPU for strict smoke checks. |
| Metrics warning says a valid metrics logging directory is missing and CWD is used. | Metrics collection is enabled without a metrics log directory. | For operational checks, construct with `collect_metrics=False` or use `fit(..., minimal=True)`. |

## TorchProphet migration warnings and errors

| Symptom | Cause | Migration recovery |
| --- | --- | --- |
| Warning or error about `_prior_scale` arguments. | Prophet prior-scale knobs are not supported for NeuralProphet regularization through the wrapper. | Use NeuralProphet regularization parameters such as `seasonality_reg`, `trend_reg`, and event/holiday regularization. |
| Warning about `mcmc_samples` or `uncertainty_samples`. | NeuralProphet does not use Prophet's Stan/MCMC uncertainty machinery. | Use NeuralProphet quantiles or conformal prediction workflows; route uncertainty details to `../evaluation-and-uncertainty/`. |
| Warning about `stan_backend`. | NeuralProphet is Torch/Lightning based, not Stan based. | Remove `stan_backend` from migrated code. |
| `NotImplementedError` about `cap` or saturating forecasts. | The wrapper does not support Prophet logistic saturation via `cap`. | Remove logistic capacity usage or redesign the forecast with native NeuralProphet trend settings. |
| `condition_name` in `add_seasonality` is not supported. | Conditional Prophet seasonalities are not implemented by the wrapper. | Use native NeuralProphet component features where possible; route detailed component redesign to `../components-and-exogenous/`. |
| Regressor `mode` does not behave like Prophet. | `TorchProphet.add_regressor` maps to a NeuralProphet future regressor and does not reliably expose Prophet regressor mode semantics. | Prefer direct `NeuralProphet.add_future_regressor(name, mode="additive" or "multiplicative")` when mode matters. |
| Plot wrapper warns about `uncertainty`, `plot_cap`, `include_legend`, `weekly_start`, or `yearly_start`. | These are Prophet plotting controls that NeuralProphet does not implement the same way. | Remove those arguments or use NeuralProphet plotting options directly. |

## Minimal recovery smoke

Run the bundled script first when operational behavior is uncertain:

```bash
python scripts/save_load_smoke.py
```

Success criteria:

- Import succeeds.
- Tiny CPU fit completes.
- Model is saved to a temporary `.np` file unless `--output-path` is supplied.
- Load uses `map_location="cpu"`.
- Prediction after load prints at least one `yhat*` column.

If this smoke passes, failures in larger tasks are likely data, modeling, plotting-export, or environment-specific rather than a broken NeuralProphet install.
