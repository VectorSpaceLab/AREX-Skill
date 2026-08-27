# Troubleshooting

## Purpose

Read this when Flow Forecast imports, configuration, data loading, plotting, or backend selection fail. The symptoms below are the most common package-specific failures observed in the repository tests and source code.

## Quick Recovery Order

1. Run [scripts/check_flow_forecast_env.py](../scripts/check_flow_forecast_env.py) to confirm imports, registry keys, and backend availability.
2. Check [references/model-overview.md](model-overview.md) for the exact `model_name`, loss, optimizer, scaler, or decoder key.
3. Check the nearest sub-skill reference for the workflow you are using.
4. Only after the config validates locally, try network/credentialed workflows such as GCS, W&B, USGS, or ASOS.

## Install / Import Problems

### `ModuleNotFoundError` for `einops`, `torchdiffeq`, `jaxtyping`, `pytorch-tsmixer`, `shap`, `plotly`, `google.cloud`, or `tensorboard`

- **Likely cause:** the selected environment is missing optional dependencies required by one or more model families or plotting helpers.
- **Next step:** install the missing dependency and rerun the root environment check script.
- **Where it matters:**
  - `einops` and `jaxtyping` for CrossViViT and catchment embedding.
  - `torchdiffeq` for Neural ODE / GR4 / hybrid physics models.
  - `pytorch-tsmixer` for `TSMixer` / `TSMixerExt`.
  - `shap` / `plotly` for explanation and plot helpers.
  - `google-cloud-storage` for GCS path handling.
  - `tensorboard` for DA-RNN logging paths.

### `cannot import name 'Deprecated' from 'wandb.proto...'` or other W&B protobuf errors

- **Likely cause:** the installed W&B / protobuf combination is incompatible with the model/runtime path.
- **Next step:** install a mutually compatible pair. The package metadata in this repository is not always aligned with the versions that are actually importable on the current Python build.
- **Symptom in this repo:** `time_model.py`, `evaluator.py`, and `deployment/inference.py` import `wandb` at module import time.

### `AttributeError: module 'wandb.util' has no attribute 'generate_id'`

- **Likely cause:** the config enables W&B logging with a newer W&B release whose utility API no longer exposes `generate_id` at the location used by this snapshot.
- **Next step:** set `wandb: false` for local smoke and non-logging runs, or install a W&B version compatible with this source snapshot after confirming protobuf compatibility.
- **Verification note:** this is an optional logging path; it should not block CPU-only training/inference guidance when W&B is disabled.

### `tb-nightly` or tensorboard-related resolution failures

- **Likely cause:** the pinned doc/runtime requirement is not available for the current Python/index combination, or `tensorboard`/protobuf versions conflict with the rest of the environment.
- **Next step:** use a compatible `tensorboard` package for local inspection and note the mismatch in the environment report. If `SummaryWriter` is needed, verify the import directly.
- **Stop condition:** if the environment cannot satisfy the runtime logging path and the task depends on it, narrow the scope or prepare a different inspection environment.

### `Error the model ... was not found in the model dict`

- **Likely cause:** `params["model_name"]` is misspelled or not one of the registry keys in `flood_forecast.model_dict_function`.
- **Next step:** read [references/model-overview.md](model-overview.md) and correct the config key.

### `bool object has no attribute 'get'` from W&B setup

- **Likely cause:** `params["wandb"]` was set to `True` instead of a mapping or `False`.
- **Next step:** use `False` for no W&B or provide a dictionary with `project`, `name`, and `tags`.

## Data And Config Problems

### `cannot supply both a tz and a timezone-naive dtype`

- **Likely cause:** a loader tried to cast a timezone-aware datetime column directly to `datetime64[ns]`.
- **Next step:** normalize the timestamp column to tz-naive datetimes first. See [sub-skills/data-preparation](../sub-skills/data-preparation/SKILL.md) and its CSV validator script.

### `forecast_history`, `forecast_length`, or `seq_len` mismatch / empty loaders

- **Likely cause:** the CSV is too short, the split indices are inconsistent, or the loader class does not match the config.
- **Next step:** validate the CSV and config with the data-preparation script before training.
- **Common fix:** ensure the loader class, `relevant_cols`, `target_col`, `sort_column`, and any temporal features all agree.

### DA-RNN `TrainData` has `features` / `targets` but `train_da` expects `feats` / `targs`

- **Likely cause:** in this repository snapshot, `flood_forecast.preprocessing.preprocess_da_rnn.TrainData` exposes `features` and `targets`, while `flood_forecast.da_rnn.train_da` expects the older `flood_forecast.da_rnn.custom_types.TrainData` fields `feats` and `targs`.
- **Next step:** wrap the preprocessed object before calling DA-RNN training, or patch the caller explicitly.
- **Minimal adapter:** `from flood_forecast.da_rnn.custom_types import TrainData as DaTrainData; raw = make_data(...); train_data = DaTrainData(raw.features, raw.targets)`.

### `No forcing attached. Call set_forcing before integrating.` or forcing shape errors

- **Likely cause:** an ODE/GR4 model was called without a forcing tensor, or the forcing/time grid has the wrong shape.
- **Next step:** check the multimodal-physics sub-skill for the expected forcing dimensions and interpolation mode.
- **Typical contract:** forcing must be `(batch_size, n_times, forcing_dim)` and times must be 1D and strictly increasing.

### `fusion must be 'concat' or 'cross_attention'`

- **Likely cause:** catchment embedding was configured with an unsupported fusion name.
- **Next step:** use one of the two documented fusion modes in the multimodal-physics sub-skill.

## Backend / Device Problems

### `PyTorch CUDA was requested but is unavailable in this process.` / `PyTorch MPS was requested but is unavailable...`

- **Likely cause:** the config explicitly requested an accelerator that the current process cannot see.
- **Next step:** switch to `device: "auto"` or `device: "cpu"`, or prepare an environment with the required backend.
- **Reminder:** CUDA/MPS support is optional for most package workflows; do not treat a CPU-only environment as evidence of accelerator success.

### `torch.cuda.is_available()` is false but the host has a GPU

- **Likely cause:** the selected environment does not have a CUDA-enabled PyTorch build or the driver is unavailable in the process.
- **Next step:** rerun the root environment check script and inspect the backend section.

## GCS / W&B / External Service Problems

### `google.cloud` / authentication / download/upload failures

- **Likely cause:** GCS helpers were called without the needed credentials or environment variables.
- **Next step:** validate the config locally first and only then enable cloud paths. If the task does not require GCS, keep it out of the runtime recipe.
- **Do not assume:** local file paths and `gs://` URIs are interchangeable.

### W&B or SHAP runs fail late in a notebook or inference session

- **Likely cause:** the environment is missing optional plotting / logging packages, or the model family is unsupported by the explanation path.
- **Next step:** confirm the exact model family in [references/model-overview.md](model-overview.md). Some models intentionally skip SHAP or have CUDA-specific caveats.

### `TypeError: tensor() got an unexpected keyword argument 'names'` in SHAP explanation

- **Likely cause:** `deep_explain_model_summary_plot` builds a named tensor using a PyTorch API shape that is not accepted in the current runtime.
- **Next step:** treat SHAP as an optional explainability path. Run deterministic inference/evaluation first, then patch or bypass the SHAP call if the task does not require explanations.
- **Training impact:** `trainer.train_function` may call post-fit evaluation that reaches SHAP on single-target non-probabilistic models; for bounded smoke runs, call `train_transformer_style` directly or use an environment/source patch that supports the explanation helper.

## Package-Specific Behavioral Quirks

- `CSVDataLoader` writes a temporary `temp_df.csv` in the current working directory during construction.
- `CSVSeriesIDLoader` returns dictionaries keyed by series index rather than a single tensor pair.
- `InferenceMode` may add `pred_<target>` columns only after inverse scaling succeeds.
- `SimpleTransformer` is not supported by the SHAP explanation helpers.
- `DARNN` has a separate training path and may require tensorboard-compatible logging support.

## When To Stop And Ask For More Information

Stop and ask the user when:

- the task needs credentials for GCS, W&B, or private datasets,
- a required accelerator backend is unavailable and the user must narrow the scope,
- a config references a model or loader family that is not present in the registry,
- the data path is remote or large enough that a local smoke test would not be representative.

## Next Reference

- [references/model-overview.md](model-overview.md)
- [data-preparation](../sub-skills/data-preparation/SKILL.md)
- [training](../sub-skills/training/SKILL.md)
- [inference](../sub-skills/inference/SKILL.md)
- [multimodal-physics](../sub-skills/multimodal-physics/SKILL.md)
