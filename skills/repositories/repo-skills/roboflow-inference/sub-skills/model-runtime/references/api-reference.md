# API reference

This reference focuses on the public runtime-facing surface of `inference-models`.
Use it to load models, inspect package options, and interpret runtime gates without reopening source files.

## Public symbols that matter here

Prefer importing from the package root when you are writing user-facing code:

```python
from inference_models import AutoModel, BackendType, Quantization
```

For environment, runtime, and registry inspection, the companion modules are also relevant:

```python
from inference_models.configuration import (
    DEFAULT_DEVICE,
    INFERENCE_HOME,
    OFFLINE_MODE,
    ONNXRUNTIME_EXECUTION_PROVIDERS,
    ROBOFLOW_API_KEY,
    ROBOFLOW_ENVIRONMENT,
)
from inference_models.developer_tools import (
    get_model_from_provider,
    get_selected_onnx_execution_providers,
    register_model_provider,
    x_ray_runtime_environment,
)
```

Use `register_model_provider()` when you need a custom weights provider name in the registry-backed load path.
`get_model_from_provider()` is useful when you want to inspect provider metadata directly without loading a model.
`get_selected_onnx_execution_providers()` shows the auto-picked ONNX execution-provider list that the loader may use.

### Runtime enums

- `BackendType`: `torch`, `torch-script`, `onnx`, `trt`, `hugging-face`, `ultralytics`, `custom`
- `Quantization`: `fp32`, `fp16`, `bf16`, `int8`, `unknown`

## AutoModel methods

### `AutoModel.describe_compute_environment()`

Prints a read-only snapshot of the current runtime:

- GPU availability and device names
- CUDA driver / runtime / toolkit availability
- TensorRT version and Python package availability
- PyTorch and torchvision versions
- ONNX Runtime version and execution providers
- Hugging Face transformers availability
- Jetson and L4T details when relevant

Use this first when a backend seems missing or a package load is unexpectedly filtered out.

### `AutoModel.describe_model(model_id, ...)`

Shows the model-level metadata and the list of available packages without loading a model.

Key arguments:

- `model_id`: Roboflow model id or registered pre-trained id
- `weights_provider`: default `"roboflow"`
- `api_key`: explicit API key or `ROBOFLOW_API_KEY`
- `pull_artefacts_size`: slower, but adds package-size information
- `weights_provider_extra_query_params` / `weights_provider_extra_headers`: advanced provider plumbing

Use this when you need to answer:

- Which backends exist for this model?
- Is the model public or private?
- How many packages are available?
- Which package id should I force?

### `AutoModel.describe_model_package(model_id, package_id, ...)`

Shows one exact package in detail.

Use this when you already know the package id and need to confirm:

- backend type
- quantization
- batch-size support
- dependency packages
- environment requirements
- package size or artefacts

### `AutoModel.from_pretrained(model_id_or_path, ...)`

Primary load entry point.

Relevant parameters grouped by purpose:

| Group | Parameters | Notes |
| --- | --- | --- |
| Source | `model_id_or_path`, `weights_provider`, `api_key` | Load from Roboflow, a local path, a cached package, or a direct checkpoint. |
| Package selection | `model_package_id`, `backend`, `batch_size`, `quantization`, `onnx_execution_providers`, `device` | These filter package candidates before ranking. `backend` and `quantization` accept a single value or a list of allowed values. |
| Load safety | `allow_untrusted_packages`, `trt_engine_host_code_allowed`, `allow_local_code_packages`, `allow_direct_local_storage_loading`, `allow_loading_dependency_models` | Use the smallest set that matches the trust boundary. |
| Cache / integrity | `verify_hash_while_download`, `download_files_without_hash`, `use_auto_resolution_cache`, `auto_resolution_cache`, `model_download_file_lock_acquire_timeout` | These control acquisition, verification, and cache reuse. |
| Advanced load plumbing | `model_type`, `task_type`, `dependency_models_params`, `point_model_directory`, `forwarded_kwargs`, `nms_fusion_preferences`, `max_package_loading_attempts`, `verbose`, `weights_provider_extra_query_params`, `weights_provider_extra_headers`, `**kwargs` | Used for checkpoint loading, dependent models, package ranking, and model-specific extras. |

Notes:

- `device` accepts a `torch.device` or a string such as `cpu`, `cuda`, or `cuda:0`.
- `batch_size` accepts a positive integer or a `(min, max)` tuple.
- `quantization` accepts a single value or a list of allowed values.
- `onnx_execution_providers` only affects ONNX packages.

#### Loading modes

- **Roboflow / remote model id**: fetch metadata, negotiate the package, download if needed, then instantiate.
- **Local directory**: if the directory has a library-style `model_config.json`, the loader uses the built-in implementation; if it declares `model_module` and `model_class`, the loader treats it as a custom code package.
- **Direct checkpoint file**: supported for RF-DETR checkpoint loading only. In that mode, `model_type` is required, the task is restricted, and the backend must resolve to `torch`.

#### Important gates

- `allow_direct_local_storage_loading=False` blocks any direct local path load.
- `allow_local_code_packages=False` blocks arbitrary code packages from local directories.
- `allow_untrusted_packages=False` drops packages marked as untrusted.
- `OFFLINE_MODE=True` restricts remote-provider loads to compatible cached packages.

## Package negotiation flow

The loader uses a predictable sequence:

1. Determine whether the input is a remote model id, a local directory, or a checkpoint path.
2. Fetch provider metadata when a remote model is requested.
3. Remove packages that do not match the model implementation or requested trust level.
4. Filter by explicit backend, batch size, quantization, runtime compatibility, and model features.
5. Rank compatible packages.
6. Load the best candidate, or fall back to offline cache when that is allowed and compatible.

### Current ranking priority

For otherwise comparable packages, the current code path prefers:

`trt` > `onnx` > `torch` > `hugging-face` > `torch-script` > `ultralytics` > `custom`

That ranking is still constrained by:

- installed extras and optional dependencies
- hardware and device compatibility
- backend-specific execution-provider requirements
- batch-size fit
- quantization fit
- trust provenance
- model-feature constraints such as fused NMS support

## Local package modes

### Library model package

A library-style local package usually contains `model_config.json` with fields such as:

- `model_architecture`
- `task_type`
- `backend_type`
- package artefacts and cache metadata

These packages are loaded through the registered model implementation for that architecture/backend.

### Custom code package

A custom package contains `model_module` and `model_class` in `model_config.json` and ships its own Python code.

This is the security-sensitive path:

- the package must be trusted
- `allow_local_code_packages=True` must be set
- the local file must exist and point to a real module file

### Direct checkpoint loading

Direct checkpoint loading is the RF-DETR-only escape hatch.

Rules:

- `model_type` is required.
- `task_type` must resolve to `object-detection` or `instance-segmentation`.
- `backend` must resolve to `torch`.
- `model_type` is only accepted for checkpoint-capable RF-DETR variants.

## Environment variables

| Variable | Meaning | Notes |
| --- | --- | --- |
| `INFERENCE_HOME` | Root cache directory | Falls back to `MODEL_CACHE_DIR`, then `/tmp/cache`. |
| `MODEL_CACHE_DIR` | Secondary cache root | Used when `INFERENCE_HOME` is unset. |
| `OFFLINE_MODE` | Startup-only offline latch | Read at import time; restart the process to change it. |
| `DEFAULT_DEVICE` | Default device string | Example values: `cpu`, `cuda`, `cuda:0`. |
| `ONNXRUNTIME_EXECUTION_PROVIDERS` | Default ONNX EP list | Comma-separated provider names. |
| `ROBOFLOW_API_KEY` | Default API key | Used when `api_key` is omitted. |
| `ROBOFLOW_ENVIRONMENT` | `prod` or `staging` | Affects API host selection. |
| `ROBOFLOW_REGION` | `us` or `eu` | Invalid values fall back to `us`. |
| `ROBOFLOW_API_HOST` | Explicit API host override | Beats region/environment selection. |

When these env vars are unset, the package also seeds `HF_HOME`, `HF_HUB_CACHE`, `HF_MODULES_CACHE`, and `YOLO_CONFIG_DIR` so implicit Hugging Face and Ultralytics runtime state stays inside the selected cache or temp directory.

## Model catalog guidance

Use the catalog workflow in this order:

1. `AutoModel.describe_model(model_id)` to see the available packages.
2. `AutoModel.describe_model_package(model_id, package_id)` to inspect one package.
3. `AutoModel.describe_compute_environment()` to verify the runtime can actually run the package.
4. Only then force `backend`, `quantization`, `batch_size`, or `model_package_id`.

If the model family is already known, do not guess the package. Inspect the catalog and let the runtime tell you which package is compatible.
