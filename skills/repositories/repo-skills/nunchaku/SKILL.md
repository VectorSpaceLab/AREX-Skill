---
name: nunchaku
description: "Route and operate the Nunchaku repo skill for CUDA-accelerated
  4-bit Diffusers image-generation workflows, quantized transformers,
  LoRA/adapters, and performance controls."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# nunchaku

Use this repo skill when a task involves the `nunchaku` Python package: loading Nunchaku quantized `.safetensors`/`.sft` assets, replacing Diffusers transformer/UNet components, choosing INT4 vs FP4 assets, debugging CUDA/build/runtime issues, composing FLUX LoRAs, or adapting Nunchaku examples/tests into bounded user workflows.

Do **not** use this skill for generic Diffusers work that does not use Nunchaku, CPU-only image generation, unsupported GPU architectures, training new models, or Qwen custom LoRA workflows. Qwen custom LoRA support is documented as under development.

## First steps

1. If Nunchaku is not installed, prefer a prebuilt wheel that matches the user's Python, PyTorch, CUDA, OS, and GPU architecture; use `references/installation-build-runtime.md` for source builds and compatibility repairs.
2. Check installation and backend with `scripts/inspect_nunchaku_install.py --device cuda:0 --pretty` or the `performance-and-memory` checker before promising CUDA-specific behavior.
3. Identify the model family and route to the smallest matching sub-skill.
4. Require explicit model assets or Hugging Face IDs from the task. Do not assume source-checkout example defaults are available.
5. Treat repo-native tests/examples as verification candidates unless they have been run in the current task.
6. If model downloads or private gated assets are required, ask for credentials/cache policy or use local paths.

## Route by task

| User task | Load |
| --- | --- |
| FLUX.1-dev/schnell/krea, FLUX Kontext, FLUX tools, FLUX v2 transformer replacement | `sub-skills/flux-pipelines/SKILL.md` |
| Qwen-Image, Qwen-Image-Edit, Qwen Lightning, Qwen 2509, Qwen ControlNet/offload | `sub-skills/qwen-image-workflows/SKILL.md` |
| Sana, Sana PAG, Z-Image, SDXL, SDXL-Turbo | `sub-skills/sana-zimage-sdxl/SKILL.md` |
| Cache, offload, FP16 attention, quantized T5 encoder, CUDA architecture/precision checks, speed/memory planning | `sub-skills/performance-and-memory/SKILL.md` |
| FLUX LoRA loading/composition/conversion, safetensor merge, IP-Adapter, PuLID | `sub-skills/lora-and-adapters/SKILL.md` |

## Core package facts

- Public root exports include `NunchakuFluxTransformer2dModel`, `NunchakuFluxTransformer2DModelV2`, `NunchakuQwenImageTransformer2DModel`, `NunchakuSanaTransformer2DModel`, `NunchakuZImageTransformer2DModel`, and `NunchakuT5EncoderModel`.
- Important non-root helpers live under package modules: `nunchaku.caching.diffusers_adapters.apply_cache_on_pipe`, `nunchaku.models.ip_adapter.diffusers_adapters.apply_IPA_on_pipe`, `nunchaku.lora.flux.compose.compose_lora`, `nunchaku.lora.flux.nunchaku_converter.to_nunchaku`, and `nunchaku.merge_safetensors.merge_safetensors`.
- Nunchaku quantized inference is a CUDA-backed workflow. CPU-only is not a full substitute for selected package capabilities.
- Precision is architecture-sensitive: current guidance is INT4 for Turing/Ampere/Ada and FP4 for Blackwell-class GPUs. Use `nunchaku.utils.get_precision()` when possible.
- Build/source installs require compatible Python, PyTorch, CUDA, compiler, and initialized submodules; prefer a prebuilt wheel when the task is only runtime usage.

## Root references and scripts

- `references/repo-provenance.md` — source commit, package version, evidence paths, and staleness signals.
- `references/repo-routing-metadata.json` — structured router metadata for managed repo-skill import tooling.
- `references/api-and-entrypoints.md` — public API, helper functions, CLI/module entry points, and native candidate map.
- `references/installation-build-runtime.md` — supported Python/CUDA/GPU/PyTorch combinations and source-build troubleshooting.
- `references/troubleshooting.md` — cross-cutting install/import, asset, backend, and workflow failure diagnoses.
- `scripts/inspect_nunchaku_install.py` — safe JSON probe for the current Python environment.

## Safety and verification boundaries

- Do not copy local checkout paths, private environment names, or construction logs into user code.
- Do not run long image generation, benchmark, or model-download workflows unless the user authorizes time, storage, credentials, and output handling.
- Native verification candidates from `tests/` and `examples/` should be selected narrowly and run only after task-specific setup is clear.
- IP-Adapter support is documented as deprecated in March 2026; surface this before recommending new long-lived IP-Adapter integrations.
