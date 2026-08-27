# Q8 Patching and VAE Patching

Related routes: [root backend requirements](../../../references/model-and-backend-requirements.md) · [core-generation](../../core-generation/SKILL.md)

Treat everything in this reference as optional and expert-only. If the user does not explicitly need Q8 or VAE patching, do not suggest it as the first fix.

## Load order

A safe mental model is:

```text
model -> Q8 patch -> Q8 LoRA loader -> sampler
vae   -> VAE patch -> decode
```

The Q8 loader only makes sense after the model has already been patched, and the VAE patch only makes sense when the Q8 backend is available.

## Node map

| Node | What it does | Hard dependency | Common failure |
| --- | --- | --- | --- |
| `LTXQ8Patch` | Patches the model transformer for Q8-style quantization | `q8_kernels` plus CUDA-capable PyTorch | The Q8 backend is missing or the model has not been patched. |
| `LTXVQ8LoraModelLoader` | Loads a Q8-aware LoRA onto the already patched model | `LTXQ8Patch` and `q8_kernels` | `LTXV Q8 Patcher is not applied to the model...` |
| `LTXVPatcherVAE` | Patches the VAE decode path and memory accounting | `q8_kernels` | Import or patch failure when the backend is unavailable. |

## What the Q8 patch controls

- `use_fp8_attention`: enable the FP8 attention path when the backend supports it.
- `quantization_preset`: choose one of the bundled presets or switch to `custom`.
- `quantize_self_attn`, `quantize_cross_attn`, `quantize_ffn`: choose which transformer parts are quantized in the custom path.

Preset meanings:

- `0.9.8`: quantize self-attention, cross-attention, and FFN.
- `ltxv2`: quantize self-attention and FFN, skip cross-attention.
- `full_bf16`: leave the transformer unquantized.
- `custom`: use the boolean toggles.

## What the Q8 LoRA loader does

- It expects the transformer to already carry the Q8 patch marker.
- It respects any quantization configuration already attached to the transformer.
- It only rewrites LoRA weights whose keys match the `lora_A` path used by the loader.
- It returns the same model handle, so downstream nodes must reuse that patched handle.

If the loader says the patcher is missing, the most likely cause is wrong node order or wiring a different model branch than the one patched upstream.

## What the VAE patch does

- The VAE patch adjusts decode memory accounting.
- It calls the backend VAE patch helper with a fixed patch block.
- It is useful when the Q8 path needs decode-side alignment, but it is not a substitute for normal VAE loading.

## Environment checks

Use [../scripts/q8_preflight.py](../scripts/q8_preflight.py) before graph debugging when the environment is unclear.

The preflight checks only:

1. `torch` import and CUDA availability.
2. `q8_kernels` importability through the same functional and integration paths that the node code expects.

Use `--json` when a caller wants machine-readable output and `--strict` when the result should fail a gate.

It does **not** load models or initialize ComfyUI graphs.

## cu130 / comfy-kitchen note

- ComfyUI may warn that a newer CUDA wheel is recommended for optimized operations on modern NVIDIA GPUs.
- A successful import on an older wheel does not mean optimized CUDA execution has been verified.
- If ComfyUI raises a `comfy_kitchen` custom-op registration error during import, treat it as an environment mismatch first and revisit the CUDA/PyTorch build before blaming the Q8 nodes.

## When not to use Q8 patches

- If the task is ordinary generation or prompt tuning, stay in the sibling skills.
- If the user only needs low VRAM behavior, prefer the standard generation loaders first.
- If `q8_kernels` is unavailable, keep the graph on non-Q8 nodes and explain that the Q8 path is unavailable.
