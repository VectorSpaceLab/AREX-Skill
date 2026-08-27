# Resource Compatibility Reference

## When to read

Read this when deciding whether a machine or BentoCloud target can run a selected OpenLLM Bento.

## Main data structures

### `Resource`

A Bento service resource spec can include:

- `memory`: numeric GB or strings like `60Gi`.
- `cpu`: CPU count.
- `gpu`: number of GPUs.
- `gpu_type`: a key from OpenLLM's accelerator map.

### `Accelerator`

OpenLLM represents accelerators with:

- `model`
- `memory_size` in GB

### `DeploymentTarget`

A target includes:

- `accelerators`
- `source` such as `local` or `cloud`
- `name`
- `price`
- `platform`

## `get_local_machine_spec`

- Returns platform `macos`, `windows`, or `linux` when detected.
- On Linux/Windows, attempts to use NVIDIA NVML through `nvidia-ml-py`.
- Returns no accelerators when NVML fails, and prints a warning.
- Warns when NVIDIA compute capability is below the recommended threshold.

## `can_run` behavior

`can_run(bento, target)` reads the first service's resource spec from `bento.yaml`.

- Platform mismatch returns `0.0`.
- Missing/empty resource specs return `0.5`.
- GPU requirements compare required GPU type memory and count against target accelerators.
- If enough GPUs are present, the result is a positive resource score.
- If a target has GPUs but the Bento has no GPU requirement, the function returns a very small positive score.
- A CPU target can return `1.0` for CPU-compatible Bentos with no GPU requirement.

## Caveats

- Resource scoring is a fit heuristic, not a benchmark.
- Actual serving still depends on model weights, dependency installation, memory fragmentation, and runtime configuration.
- A CPU import check is not proof that a GPU-required Bento can serve.
