# Setup and Backend Troubleshooting

Use this reference when verl imports, package checks, accelerator visibility, or optional backend stacks fail. Start with the safe bundled helper:

```bash
python sub-skills/setup-and-backends/scripts/check_verl_environment.py --pretty --include-cuda --check-pip
```

The helper avoids network calls, Docker actions, Ray jobs, model downloads, and local path disclosure.

## Fast triage sequence

1. Confirm Python is `>=3.10`.
2. Confirm `verl` package metadata and import status.
3. Confirm core dependency versions: `torch`, `tensordict`, `ray`, `transformers`, `hydra-core`, and `omegaconf`.
4. Confirm optional backend packages only for the requested backend: `vllm`, `sglang`, `mbridge`, `flash_attn`, `liger_kernel`, `tensorrt_llm`, `torch_npu`.
5. If executing GPU/NPU/ROCm workloads, confirm accelerator visibility and torch build; do not treat CPU-only import success as runtime validation.
6. Run `pip check` or equivalent only after backend package installation stabilizes.

## CPU-only inspection vs runtime failure

A CPU-only environment can be healthy for:

- Importing `verl`, `verl.protocol`, trainer config modules, `verl.trainer.main_ppo`, `verl.model_merger`, and tool base modules.
- Reading package metadata.
- Inspecting Hydra config dataclasses and Python APIs.
- Running safe static or import-only checks.

A CPU-only environment is not enough for:

- vLLM, SGLang, TensorRT-LLM, flash-attn, or Liger kernel runtime.
- CUDA graph, NCCL/HCCL/RCCL communication, or Ray accelerator resource scheduling.
- Megatron/MCore training with Apex, TransformerEngine, or accelerator kernels.
- Any claim that a rollout engine works with real model weights.

If a user says "base install works but vLLM rollout fails," check for an installed supported vLLM version and a CUDA-capable torch build before changing rollout configuration.

## Known version-sensitive packages

### tensordict

verl currently declares `tensordict>=0.8.0,<=0.10.0,!=0.9.0`. Treat `tensordict` outside that range as a first-class suspect. Backend installers may downgrade or upgrade it. If a latest `tensordict` release causes import or TensorDict behavior changes, pin back into the declared range before debugging verl internals.

### torch and backend installers

vLLM, SGLang, torch extension packages, and NPU/ROCm wheels can replace torch. Install backend stacks first when they have strict torch expectations, then install verl without dependencies when appropriate. After every backend install, re-check torch, backend package versions, and `pip check`.

### transformers

Package metadata excludes `transformers==5.6.0` because that release has a broken flash-attention path for sink-less models. If flash-attention errors appear around Qwen/Llama-style models, verify the transformers version before changing model code.

### ray

verl requires `ray[default]>=2.41.0`. Accelerator resource behavior also depends on visible-device env vars and platform plugin detection. If Ray workers see different devices from the driver, inspect `CUDA_VISIBLE_DEVICES`, `HIP_VISIBLE_DEVICES`, `ROCR_VISIBLE_DEVICES`, `ASCEND_RT_VISIBLE_DEVICES`, and the relevant `RAY_EXPERIMENTAL_NOSET_*` variables.

## Backend-specific symptoms

### vLLM rollout fails after a base install

Likely causes:

- `vllm` is not installed because base verl does not include optional extras.
- `vllm` version is outside the supported range or conflicts with torch.
- CUDA is unavailable, too old, or torch is CPU-only.
- `tensordict` was overwritten outside verl's declared range.
- Using older `vllm 0.7.x`, which project docs warn can cause OOMs and unexpected errors.

Suggested checks:

```bash
python sub-skills/setup-and-backends/scripts/check_verl_environment.py --pretty --include-cuda --optional vllm tensordict torch
```

If CUDA and vLLM are absent, recommend a Docker/backend install path rather than editing training configs. If CUDA is present but vLLM errors during startup, collect vLLM, torch, CUDA runtime, driver, and `VLLM_USE_V1`/rollout env settings.

### SGLang setup conflicts with torch

The `sglang` extra pins `sglang[srt,openai]==0.5.8` and `torch==2.9.1`. Install SGLang in a fresh environment or before other torch-sensitive packages. If an existing environment uses a different torch for vLLM or NPU, do not mix stacks casually; recommend a separate environment or container.

### Megatron/MCore import or runtime issues

The `mcore` extra installs `mbridge`, but real Megatron runtime may also need compatible CUDA/NPU packages, Apex, TransformerEngine, and communication libraries. Verify the user actually needs Megatron scalability; FSDP/FSDP2 is recommended for research and prototyping.

### flash-attn or GPU kernels missing

`flash-attn` and `liger-kernel` are optional under the `gpu` extra and are commonly provided by Docker images. Missing kernel packages in CPU inspection environments are expected. In custom CUDA environments, verify CUDA, torch ABI, compiler availability, and build isolation flags before assuming a verl bug.

### TensorRT-LLM missing

TensorRT-LLM is optional through the `trtllm` extra with `tensorrt-llm>=1.2.0rc6`. It requires a compatible NVIDIA runtime stack. Do not install it into a CPU-only inspection environment unless the user explicitly needs package-level inspection.

## Platform detection and environment variables

verl platform detection uses:

1. `VERL_PLATFORM` override.
2. Registered platform probes for built-ins.
3. NVIDIA fallback when nothing is detected.

Built-in platform names are `nvidia`, `amd`, and `huawei`.

NVIDIA notes:

- Device type is `cuda`.
- Default communication backend is `nccl`, or `flagcx` when `USE_FLAGCX=1`/`true`.
- CUDA rollout env includes `NCCL_CUMEM_ENABLE=0` to avoid known synchronization issues in some vLLM paths.

AMD ROCm notes:

- PyTorch ROCm still exposes `torch.cuda`; device strings may be `cuda` even though vendor is AMD.
- Platform detection checks `torch.version.hip` and `rocm-smi` when available.
- Ray no-set variables include CUDA, HIP, and ROCR visible-device variants.
- `SGLANG_USE_AITER` defaults to `1` in the ROCm platform integration unless overridden.

Huawei Ascend notes:

- Detection depends on `torch_npu` importability and `torch.npu` availability.
- Default communication backend is `hccl`, or `flagcx` when requested.
- Visible-device env var is `ASCEND_RT_VISIBLE_DEVICES`.
- Ray no-set variable is `RAY_EXPERIMENTAL_NOSET_ASCEND_RT_VISIBLE_DEVICES`.
- NPU rollout env includes `NCCL_CUMEM_ENABLE=0` and `VLLM_ASCEND_AUTO_DETECT_QUANTIZATION=0`; task queue behavior can be controlled through `VLLM_ASCEND_TASK_QUEUE_ENABLE`.

## Docker and unsafe operations

Do not run Docker build, Docker run, package installs, GPU burn-in, or distributed Ray jobs without user approval. For skill-driven diagnosis, gather safe metadata first. If the issue requires real accelerator validation, ask for the target platform, backend, and permission to run the relevant commands.

## Difficult synthetic usability cases

Use these as high-value tests for future skill verification:

- CPU-only base install passes core imports and `pip check`, but the user asks why vLLM rollout fails. A good answer distinguishes inspection success from runtime readiness, checks optional `vllm`, torch CUDA availability, CUDA `>=12.8`, and `tensordict`, then recommends a backend container or `.[vllm]` install rather than editing rollout code.
- A user reports failures after upgrading to the latest `tensordict`. A good answer identifies verl's declared `tensordict>=0.8.0,<=0.10.0,!=0.9.0` constraint, checks the active version, and recommends pinning within the supported range before investigating DataProto or trainer internals.
