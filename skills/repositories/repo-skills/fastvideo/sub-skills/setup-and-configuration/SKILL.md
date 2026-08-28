---
name: setup-and-configuration
description: "Handles FastVideo installation, platform and backend selection, model registry lookup, presets, configuration schemas, and environment diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Setup and configuration

Use for installation, Python/platform checks, CUDA/MPS/ROCm choice, model-ID
support, preset selection, configuration parsing, and import or dependency
failures.

## Workflow

1. Identify OS, architecture, Python version, GPU/driver/toolkit, and whether
   the task needs inference, serving, preprocessing, training, or evaluation.
2. Choose an isolated Python 3.10–3.12 environment. NVIDIA installs select
   `UV_TORCH_BACKEND=cu126` or `cu130`; Apple Silicon follows MPS guidance;
   ARM NVIDIA may require a source kernel build.
3. Install only the needed package extras. Do not install Linux CUDA-only
   extensions on MPS, and do not assume a CPU import proves CUDA support.
4. Run the bundled [environment diagnostic](scripts/check_environment.py).
5. Use [configuration reference](references/configuration.md) to build typed
   nested configs and [model reference](references/model-overview.md) to check
   model families, workloads, and backend constraints.

The package exports `VideoGenerator`, `PipelineConfig`, `SamplingParam`, and
`__version__`. The CLI exposes `generate`, `serve`, `router-serve`, `bench`,
and `eval`.

## Boundaries

Route generation flags and optimization choices to [inference](../inference/SKILL.md);
route server config to [serving](../serving/SKILL.md); route data/training
requirements to [training-and-data](../training-and-data/SKILL.md). This route
owns platform and config validation, not model-weight execution.

## Checks

A successful import is only a package check. Also verify the selected torch
backend, required optional modules, model-weight access, available VRAM, and
whether the chosen model/optimization is registered. Read
[setup troubleshooting](references/troubleshooting.md) for recovery steps.
