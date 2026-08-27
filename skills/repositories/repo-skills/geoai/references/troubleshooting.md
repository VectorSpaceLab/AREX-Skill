# Cross-Cutting Troubleshooting

## Purpose

Read this when a GeoAI task fails before the workflow is clearly owned by a sub-skill. Once you identify the failing surface, continue in the nearest sub-skill troubleshooting reference.

## `import geoai` fails

**Symptoms**

- `ModuleNotFoundError: No module named 'geoai'`
- `PackageNotFoundError: geoai-py`
- `python -m geoai.cli --help` cannot find the module

**Likely causes**

- The environment does not have `geoai-py` installed.
- The wrong Python executable is being used.
- An editable install was attempted from the wrong checkout.

**Recovery**

1. Install or reinstall the package with `pip install geoai-py`.
2. Confirm with `python -c "import geoai; print(geoai.__version__)"`.
3. Run `python scripts/check_geoai_env.py --check-cli` from this skill directory if the bundled helper is available.

## A specific module fails after `import geoai` works

**Symptoms**

- `AttributeError: module 'geoai' has no attribute ... (failed to import ...)`
- `ModuleNotFoundError` for `rfdetr`, `onnxruntime`, `strands`, `vllm`, `terratorch`, `neatnet`, `opticallyshallowdeep`, or another optional dependency

**Likely causes**

GeoAI uses lazy imports and optional extras. The base import can succeed while a workflow-specific module still needs an extra.

**Recovery**

1. Identify the owning sub-skill in [top-level API map](top-level-api-map.md).
2. Install only the extra required for that workflow.
3. Re-run the smallest read-only check from the owning sub-skill, not a full model run.

## CLI command is missing or behaves unexpectedly

**Symptoms**

- `geoai: command not found`
- CLI help does not list `info`, `download`, and `pipeline`
- `geoai pipeline show` fails before reading a config

**Recovery**

1. Prefer `python -m geoai.cli --help` to bypass shell PATH issues.
2. If `python -m geoai.cli --help` works, reinstall or refresh console scripts in the environment.
3. For pipeline config errors, route to `sub-skills/geospatial-data-pipelines` and use its bundled validator.

## CUDA or accelerator confusion

**Symptoms**

- `torch.cuda.is_available()` is `False` on a machine with a GPU.
- A model workflow runs on CPU unexpectedly.
- CUDA import or allocation errors occur before model inference/training.

**Likely causes**

- CPU-only PyTorch build.
- Driver/runtime mismatch.
- Container or process cannot see the GPU.
- The workflow can run on CPU but the user's expected scale needs GPU.

**Recovery**

1. Run `python scripts/check_geoai_env.py --check-cuda`.
2. Confirm the PyTorch build, CUDA runtime, device count, and a tiny allocation.
3. Do not treat CPU import success as proof of GPU readiness.
4. Continue in the inference, training, or foundation-model sub-skill that owns the actual model workflow.

## Raster/vector or GDAL/PROJ failure

**Symptoms**

- `rasterio` cannot open a file.
- CRS is missing or mismatched.
- Vectorization/rasterization output is empty or spatially shifted.
- Bbox coordinates appear reversed or outside the raster bounds.

**Recovery**

Route to `sub-skills/geospatial-data-pipelines`. Use its I/O smoke helper to compare CRS, bounds, band counts, and feature counts before running downloads, tiling, or model inference.

## Foundation model name is unknown

**Symptoms**

- `ValueError: Unknown foundation model ...`
- A Hugging Face repository ID is passed where GeoAI expects a registry key.

**Recovery**

Route to `sub-skills/foundation-models-embeddings-vlms`. Use its registry reporter to normalize the name and distinguish metadata lookup from model-weight loading.

## QGIS, MCP, or agent integration failure

**Symptoms**

- QGIS plugin dependency installer fails.
- MCP client config starts the wrong command or accesses the wrong sandbox directory.
- `geoai.agents` imports fail with missing `strands` packages.
- Provider calls need API keys or external model services.

**Recovery**

Route to `sub-skills/integrations-agents-qgis-mcp`. Use its read-only config and dependency probes before mutating a QGIS profile, installing packages, starting a server, or exposing credentials.

## When to stop and ask

Stop and ask the user before:

- Installing broad optional extras or GPU packages in a user-owned environment.
- Downloading model weights or datasets.
- Starting long training or inference.
- Starting an MCP server or vLLM service.
- Mutating a QGIS profile, plugin directory, or managed environment.
- Performing credentialed Hub/QGIS upload operations.
