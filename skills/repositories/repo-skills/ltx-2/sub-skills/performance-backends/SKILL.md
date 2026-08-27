---
name: performance-backends
description: "Helps agents choose and troubleshoot LTX-2 performance backends
  for CUDA readiness, FP8/NVFP4, block streaming, torch.compile, DiffVAE
  backends, ltx-kernels, and multi-GPU execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Performance Backends

Use this sub-skill when the request is about making LTX-2 faster, smaller, or more parallel: CUDA readiness, FP8 / NVFP4 tradeoffs, offload, block streaming, `torch.compile`, DiffVAE backend selection, `ltx-kernels`, or multi-GPU latency paths.

It is for choosing and troubleshooting backend options, not for composing a generation command or training launch.

## Route away

- Command construction for inference pipelines → `../inference-pipelines/SKILL.md`
- Training launch/configuration → `../training-workflows/SKILL.md`
- Low-level builders, model objects, or decoder internals → `../core-components/SKILL.md`

## Fast workflow

1. Read [backend-matrix.md](references/backend-matrix.md) to separate the verified CUDA baseline from optional accelerator paths.
2. Run [scripts/check_backend_readiness.py](scripts/check_backend_readiness.py) to inspect the current Python/CUDA/device stack without building or downloading anything.
3. If the question touches compiled kernels, read [kernels-and-accelerators.md](references/kernels-and-accelerators.md).
4. If it involves SP, TDP, distributed decode, Gemma sharding, or MGPU controllers, read [multigpu.md](references/multigpu.md).
5. If something fails or a backend is missing, use [troubleshooting.md](references/troubleshooting.md) to map the symptom to a safe fallback.

## What this sub-skill covers

- CUDA parser/runtime readiness versus optional accelerator readiness.
- Memory-relief choices: `--offload`, `--quantization`, block streaming, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- `torch.compile` tradeoffs, resident-weight requirements, and dynamic-shape caveats.
- Optional accelerator readiness: `ltx-kernels`, NATTEN, FlashAttention, and Blackwell-only paths.
- DiffVAE backend selection: `DiffVAEMode`, NATTEN, Triton, eager, and Blackwell DSL.
- `ltx-kernels` surfaces: all2all, blockwise FP8/FP6, NVFP4, and VAE CuTe DSL.
- Multi-GPU latency paths: SP, TDP, distributed decoder, distributed Gemma, and the MGPU controller.

## What it does not own

- It does not build kernels, install packages, download checkpoints, or run generation/training.
- It does not decide the exact CLI flag order for a pipeline; that belongs to the inference-pipelines sub-skill.
- It does not author low-level API objects or patch model internals; route those questions to core-components.
- It does not install packages or compile kernels; it only explains the backend choice and the safe fallback.

## Verified baseline

A CUDA smoke check passed with `torch 2.13.0+cu132` on an A100 host. The verification did **not** build `ltx-kernels`, so optional accelerator claims should be treated as unverified until the local host checks them.

## Read next

- [references/backend-matrix.md](references/backend-matrix.md)
- [references/kernels-and-accelerators.md](references/kernels-and-accelerators.md)
- [references/multigpu.md](references/multigpu.md)
- [references/troubleshooting.md](references/troubleshooting.md)
