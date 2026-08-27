# Chronos Forecasting troubleshooting

Use this repo-level reference for cross-cutting install, import, model-loading, optional dependency, backend, and routing failures. Use sub-skill troubleshooting files for workflow-specific errors.

## Import or metadata failures

Symptoms:

- `ModuleNotFoundError: No module named 'chronos'`.
- installed distribution cannot be found.
- version is different than expected.

Fix:

1. Install `chronos-forecasting` into the Python environment that will run the task.
2. Run `python -c "import chronos; print(chronos.__version__)"`.
3. If using a local checkout, prefer an editable install only for development; public task guidance should use the package install command unless the user explicitly works on source.
4. Use `python -m pip check` when dependency conflicts are suspected.

## Unknown or wrong pipeline family

Symptoms:

- a Chronos-2 method such as covariate-aware `predict_df` is missing,
- a loaded model returns `ChronosPipeline` or `ChronosBoltPipeline` when Chronos-2 was expected,
- `BaseChronosPipeline.from_pretrained` raises `Not a Chronos config file` or `unknown pipeline class`.

Fix:

- Load through `BaseChronosPipeline.from_pretrained(...)` only for Chronos model anchors.
- Print `type(pipeline).__name__` and `pipeline.forecast_type`.
- Route Chronos-2, Bolt, and original model-family tasks to the matching sub-skill.
- Confirm that a local directory contains a compatible Transformers config with Chronos fields.

## Hugging Face or S3 loading failures

Symptoms:

- network timeout,
- unauthorized/private model errors,
- S3 credential errors,
- `boto3` missing,
- cache corruption or stale files.

Fix:

1. Ask whether downloads/network are allowed.
2. For Hugging Face IDs, confirm model name, access permissions, and optional token configuration.
3. For `s3://` URIs, install/configure `boto3` and credentials; use `force_s3_download=True` only when the user wants to refresh the cache.
4. Try a local model directory if offline.
5. Do not proceed to benchmark/training/deployment until model loading is stable.

## Optional dependency missing

- `peft`: needed for Chronos-2 LoRA adapter loading and LoRA fine-tuning.
- `fev` and `datasets`: needed for `predict_fev` and benchmark workflows.
- `boto3`: needed for S3 model loading.
- `pyarrow`: needed for parquet data examples.
- GluonTS/dev stack: needed for maintainer training and KernelSynth workflows.

Install the smallest option required by the active sub-skill, not all extras by default.

## Backend or device mismatch

Symptoms:

- `torch.cuda.is_available()` is false when CUDA was expected,
- `CUDA out of memory`,
- dtype errors on CPU,
- slow inference/training.

Fix:

- Use CPU for correctness smokes and small examples when acceptable.
- For CUDA, install a compatible PyTorch CUDA wheel and verify a tiny CUDA tensor allocation.
- Lower `batch_size`, `context_length`, or `prediction_length` for memory issues.
- Use `torch_dtype="float32"` for conservative CPU runs and `bfloat16` only when the device supports it.
- Do not claim GPU coverage unless it was actually tested.

## Data and schema errors

Use [sub-skills/data-formats-and-validation/](../sub-skills/data-formats-and-validation/) when errors mention missing columns, frequency inference, duplicate timestamps, future covariate row counts, list-of-dicts keys, or covariate lengths.

## Side-effecting workflow gates

Stop and ask for explicit user confirmation before:

- downloading large models/datasets,
- running training/fine-tuning beyond tiny smoke tests,
- launching distributed/GPU jobs,
- creating cloud endpoints,
- writing or overwriting checkpoints,
- pushing models to a hub or cloud bucket, or
- using credentials/tokens.
