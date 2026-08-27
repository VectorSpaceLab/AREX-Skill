# Troubleshooting

Use this reference when model negotiation, loading, or backend selection fails.

## Start with these probes

1. `python scripts/describe_compute_environment.py`
2. `AutoModel.describe_model(model_id)`
3. `AutoModel.describe_model_package(model_id, package_id)`
4. `AutoModel.from_pretrained(..., verbose=True)`

These four steps usually tell you whether the problem is missing dependencies, incompatible hardware, a bad package choice, or a bad local package.

## Missing backend packages or extras

### Symptom

- `MissingDependencyError`
- `ModelPackageAlternativesExhaustedError`
- backend-specific import errors during load

### Likely cause

The model published a package for a backend that is not installed in this environment.

### Fix

- Install the matching backend extra from `references/backends.md`.
- Re-run `AutoModel.describe_compute_environment()`.
- If you are on NVIDIA GPU hardware, make sure the TensorRT or CUDA runtime actually matches the package.

## Unknown backend, quantization, or batch size values

### Symptom

- `UnknownBackendTypeError`
- `UnknownQuantizationError`
- `InvalidRequestedBatchSizeError`

### Likely cause

The caller used a value that is not supported by the loader.

### Supported values

- Backends: `torch`, `torch-script`, `onnx`, `trt`, `hugging-face`, `ultralytics`, `custom`
- Quantization: `fp32`, `fp16`, `bf16`, `int8`, `unknown`
- Batch size: positive integer or `(min, max)` tuple with `min <= max`

### Fix

- Use the exact enum value or the exact lower-case string.
- Use a positive integer or a 2-tuple for batch size.
- If you are unsure, leave the parameter unset and inspect the catalog first.

## Invalid environment variables or runtime configuration

### Symptom

- `InvalidEnvVariable`
- unexpected runtime device selection
- ONNX provider mismatch
- offline mode that does not seem to change

### Likely cause

The environment variable is malformed or was changed after import.

### Fix

- Boolean env vars must be `true` or `false`.
- `ONNXRUNTIME_EXECUTION_PROVIDERS` must be a comma-separated list.
- `DEFAULT_DEVICE` must be a valid `torch.device` string such as `cpu` or `cuda:0`.
- `OFFLINE_MODE` is startup-only; restart the process to change it.
- If `ROBOFLOW_REGION` is invalid, the runtime falls back to `us`.

## Local package trust gates

### Symptom

- `DirectLocalStorageAccessError`
- `ForbiddenLocalCodePackageAccessError`

### Likely cause

A local directory or custom code package was blocked by a security gate.

### Fix

- Set `allow_direct_local_storage_loading=True` only when you truly want to load local paths.
- Set `allow_local_code_packages=True` only for trusted code packages.
- Verify `model_config.json` exists and points to the right module/class.
- If the package came from an untrusted provider, either trust it explicitly or choose another package.

## Cache and offline-mode failures

### Symptom

- `ModelRetrievalError` in offline mode
- model loads online but fails offline
- cache hit disappears after changing a parameter

### Likely cause

The cache was not warmed with the same runtime constraints, or the package was warmed under a different key / provider / device / backend / batch / quantization combination.

### Fix

Warm the cache again with the exact settings you intend to use offline:

- `weights_provider`
- `api_key` state
- `backend`
- `batch_size`
- `quantization`
- `device`
- `onnx_execution_providers`
- dependency-model settings
- trust settings

If the cache is stale or corrupted, clear the relevant cache directory under `INFERENCE_HOME` and re-warm it.

## Package compatibility failures

### Symptom

- `NoModelPackagesAvailableError`
- `ModelPackageAlternativesExhaustedError`
- `ModelPackageNegotiationError`

### Likely cause

No published package survived the implementation, trust, backend, batch-size, quantization, runtime, or feature filters.

### Fix

- Loosen `backend`, `batch_size`, or `quantization`.
- Install the missing backend extras.
- Check the package’s device and execution-provider requirements.
- Use `AutoModel.describe_model_package(...)` to inspect the package you were trying to force.

## Checkpoint loading failures

### Symptom

- `MissingModelInitParameterError`
- `InvalidModelInitParameterError`

### Likely cause

A direct checkpoint path was loaded without the required metadata.

### Fix

- Provide `model_type`.
- Use a supported RF-DETR checkpoint type.
- Keep `task_type` within the supported checkpoint tasks.
- Keep the backend on `torch` for checkpoint loading.

## Runtime inference failures after load

### Symptom

- `ModelRuntimeError`
- `ModelInputError`
- `InvalidParameterError`
- device mismatch errors

### Likely cause

The model loaded successfully, but the input shape, device, or backend-specific runtime constraint is wrong.

### Fix

- Check input tensor / array shape and channel order.
- Make sure TensorRT runs on CUDA.
- Make sure ONNX has a valid execution-provider list.
- Make sure the input device matches the loaded model’s device.
- Re-check the model page for task-specific input rules.

## Corrupted or malformed package metadata

### Symptom

- `CorruptedModelPackageError`

### Likely cause

The package metadata, cache manifest, or `model_config.json` is malformed or incomplete.

### Fix

- Re-download or re-warm the package.
- Clear the corrupted cache entry.
- Re-run `AutoModel.describe_model(...)` to confirm the upstream package metadata is still valid.
- If the package came from a provider, report the issue with the package id and full traceback.

## What to collect before escalating

Include all of the following:

- model id and package id
- backend, batch size, quantization, and device
- `AutoModel.describe_compute_environment()` output
- `AutoModel.describe_model(...)` output
- `AutoModel.describe_model_package(...)` output if you have one
- `ONNXRUNTIME_EXECUTION_PROVIDERS`
- `OFFLINE_MODE`, `INFERENCE_HOME`, `DEFAULT_DEVICE`, `ROBOFLOW_ENVIRONMENT`
- full traceback and the exact `from_pretrained(...)` call

## Quick triage questions

- Did the package exist on the model page?
- Did the runtime show the backend as installed?
- Did the model load from a path you meant to be local?
- Did you change any environment variable after import?
- Are you forcing a package or backend that the catalog does not publish?
