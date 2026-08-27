---
name: model-backends
description: "Select and troubleshoot XTuner V1 model configs, MoE/VLM backends,
  FSDP/TP/EP/HSDP sizing, FP8, attention, routers, dispatchers, and optional
  accelerators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XTuner model-backends

Use this sub-skill when the task is about XTuner V1 model configuration or backend capability: selecting dense, MoE, or multimodal model config classes; aligning `FSDPConfig` with model parallel settings; choosing attention/router/dispatcher options; enabling FP8; or diagnosing optional acceleration gaps.

## Scope and routing

Use this skill for:

- `xtuner.v1.model` config classes and `get_model_config` / `get_model_config_from_hf` helpers.
- Qwen3 dense and MoE, Qwen3.5-VL, InternVL, InternS1, GPT-OSS, DeepSeek/GLM-style MoE families.
- FSDP, tensor parallel (`tp_size`), expert parallel (`ep_size`), HSDP, MoE dispatchers, grouped GEMM, attention backend choices, FP8, optimizer/loss config interactions that affect backend sizing.
- Backend diagnostics that are safe without launching training.

Route elsewhere:

- Training launch commands, checkpoint/resume workflows, logs, and trainer construction details -> training.
- Dataset schemas, tokenization, packing, JSONL/media validation -> data-preparation.
- RL advantage, rollout engines, Ray cluster topology, RL losses beyond backend import checks -> reinforcement-learning.
- Legacy `xtuner` CLI/config-zoo tasks -> cli-and-tools.

## Operating workflow

1. **Classify the model family.** Decide whether the requested work is text dense, text MoE, or compose/VLM. Use `get_model_config(alias)` only for aliases known to XTuner; instantiate concrete classes directly for unaliased variants.
2. **Resolve required backend features.** Mark each requested feature as config-only, CPU/import-checkable, CUDA/NPU-required, or optional-accelerator-required. Do not treat an import check as proof of acceleration.
3. **Choose parallelism conservatively.** Start with FSDP. Use TP only when memory requires it. For MoE, keep `model_cfg.ep_size` aligned with `FSDPConfig(ep_size=...)`; choose a dispatcher only when `ep_size > 1`. HSDP requires `ep_size == 1`.
4. **Probe safely before claiming support.** Run the bundled backend checker from this sub-skill tree:

   ```bash
   python scripts/check_xtuner_backend.py
   python scripts/check_xtuner_backend.py --json --expect-cuda
   python scripts/check_xtuner_backend.py --check-optional --json
   ```

   The checker reports Torch/CUDA visibility, optional imports, FP8 hardware indicators, and selected XTuner imports. It does not run kernels, build models, or verify training throughput.
5. **Use the references for decisions and troubleshooting.** Keep long API tables, backend constraints, and failure modes in:
   - [Model and backend reference](references/model-and-backend-reference.md)
   - [API reference](references/api-reference.md)
   - [Troubleshooting](references/troubleshooting.md)

## Quick decision guide

- **Qwen3 dense / dense VLM:** simpler backend surface; no expert routing or MoE dispatcher. Use `Qwen3Dense8BConfig`, `Qwen3Dense4BConfig`, `Qwen3Dense0P6BConfig`, `Qwen3VLDense4BConfig`, `Qwen3VLDense8BConfig`, `InternS1MiniConfig`, or InternVL dense configs as appropriate. `ep_size` should stay `1`.
- **Qwen3 MoE / MoE VLM:** adds routed experts, balancing/z/aux losses, grouped GEMM, and possible expert-parallel all-to-all. Use `Qwen3MoE30BA3Config`, `Qwen3MoE235BA22Config`, Qwen3-VL MoE, Qwen3.5-VL MoE, InternS1, GPT-OSS, DeepSeek, or GLM MoE configs. Align `ep_size` in both model and FSDP config.
- **TP vs EP:** TP can reduce memory pressure but reduces per-rank matrix sizes and can hurt efficiency. EP partitions MoE experts but does not remove attention/activation memory and introduces all-to-all communication. Prefer the smallest TP/EP values that satisfy memory and topology constraints.
- **FP8:** requires a real compatible CUDA backend, Hopper-class or newer device capability for effective FP8, and optional libraries such as AdaptiveGEMM for tile-wise FP8 linear/grouped-linear modules. FP8 import or config construction alone is not acceleration proof.
- **Attention:** `flash_attention` may fall back to `flex_attention` when `flash-attn` is missing. Use `eager_attention` only for debugging/HF parity or when fused attention is unavailable.

## Non-negotiable verification rules

- Never claim FlashAttention, bitsandbytes GPU kernels, DeepEP, grouped GEMM, AdaptiveGEMM, FP8, NPU, or Ray-backed capability unless the relevant optional dependency and hardware path were actually checked.
- A CPU-only check is useful for config/import sanity but is not a CUDA/NPU or performance verification.
- If a backend is optional and missing, provide a safe fallback plan and state the unverified gap explicitly.
