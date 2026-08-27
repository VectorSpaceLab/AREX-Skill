---
name: scaling-and-backends
description: "Choose and diagnose TRL scaling, memory, kernel, PEFT, and vLLM
  backends without launching expensive training or serving jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scaling and Backends

Use this sub-skill when a TRL task is about making training fit, run faster, or use the right distributed/inference backend. This includes Accelerate launch topology, FSDP, DeepSpeed, PEFT/LoRA/quantization, Liger, Unsloth, Kernels Hub attention implementations, activation offloading, and vLLM server or colocated generation.

Route elsewhere when the user is choosing the training algorithm or reward objective, writing CLI/dataclass syntax in detail, or integrating environment-specific experiment systems. Keep this sub-skill focused on backend decisions, resource constraints, and safe diagnostics.

## Quick Routing

- For launch topology, FSDP, DeepSpeed, sequence/context parallelism, mixed precision, PEFT, quantization, kernels, Unsloth, RapidFire, or memory reduction, start with [backend-selection](references/backend-selection.md).
- For online generation acceleration with `use_vllm=True`, server vs colocate mode, server flags, weight sync, ports, and continuous batching implications, use [vllm-reference](references/vllm-reference.md).
- For failed imports, missing extras, CUDA unavailability, vLLM URL timeouts, OOM, parallel-size mismatches, PEFT/quantization package errors, and service constraints, use [troubleshooting](references/troubleshooting.md).
- Before recommending optional extras or hardware-heavy commands, run the safe diagnostic wrapper: `python scripts/check_optional_backends.py`. It only checks imports, versions, and visible accelerator facts; it does not start servers, train, download models, or allocate large tensors.

## Safe Backend Workflow

1. Identify the bottleneck: model does not fit, generation is slow, launch needs more GPUs, kernels are missing, or service connectivity is broken.
2. Check installed optional backends and visible accelerator state with `scripts/check_optional_backends.py` before suggesting vLLM, DeepSpeed, PEFT, bitsandbytes, Liger, Unsloth, or kernels-specific paths.
3. Pick the least invasive backend that addresses the bottleneck: batch/sequence reduction first, PEFT/quantization next, kernels/Liger for speed-memory wins, FSDP/DeepSpeed for sharding, and vLLM only for online trainers with generation bottlenecks.
4. Keep trainer semantics with the relevant algorithm sub-skill. This sub-skill can say whether `GRPOConfig(use_vllm=True, vllm_mode="server")` is appropriate, but not redesign the GRPO reward objective.
5. Do not run `accelerate launch`, `trl vllm-serve`, training scripts, model downloads, or Docker/service commands unless the user explicitly approves the resource use and hardware assumptions.

## High-Value Defaults

- Use `accelerate launch` for multi-GPU TRL training; use the distilled config families in [backend-selection](references/backend-selection.md) rather than copying source repo paths.
- Use FSDP2/context parallelism for long-context memory pressure when the environment has modern Accelerate/PyTorch support.
- Use DeepSpeed ZeRO when optimizer/gradient/parameter sharding or offload is the main need and DeepSpeed is already available or can be installed.
- Use PEFT/LoRA or QLoRA when the user can trade full fine-tuning for adapter training and lower memory.
- Use vLLM server mode when online RL generation is the bottleneck and separate generation GPUs or a separate service are available; use colocate only when GPUs are limited and resource contention is acceptable.
