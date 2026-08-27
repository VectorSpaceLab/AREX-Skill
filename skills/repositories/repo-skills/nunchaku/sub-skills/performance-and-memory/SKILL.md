---
name: performance-and-memory
description: "Use Nunchaku cache, offload, precision, attention, qencoder, CUDA
  sanity, and verification-planning controls for speed and memory work."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Nunchaku performance and memory controls

Use this sub-skill when a task asks how to reduce VRAM, select quantized precision, enable cache acceleration, choose attention/offload settings, check CUDA compatibility, or plan bounded speed/memory verification for an installed Nunchaku runtime.

Do **not** use this sub-skill for full image-generation task templates. Route family-specific pipelines to the model-family sub-skills and use this one only for composable performance fragments.

## Start with a safe runtime check

Run the bundled checker in the user's current Python environment before recommending architecture-specific settings:

```bash
python scripts/check_nunchaku_cuda.py --device cuda:0 --pretty
```

The checker imports only `torch`, `nunchaku`, and lightweight API modules, allocates at most a scalar CUDA tensor unless `--skip-allocation` is set, and never downloads model assets.

## Fast routing

| User need | Use |
| --- | --- |
| Pick INT4 vs FP4 weights | `nunchaku.utils.get_precision(device="cuda:0")`; Blackwell SM 120/121 uses FP4, Turing/Ampere/Ada SM 75/80/86/89 use INT4. |
| Reduce FLUX VRAM | Load `NunchakuFluxTransformer2dModel.from_pretrained(..., offload=True)` and pair it with Diffusers `pipeline.enable_sequential_cpu_offload()`; avoid manual `.to("cuda")` in this mode. |
| Reduce Qwen-Image VRAM | Use Diffusers CPU offload when VRAM is sufficient; for very low VRAM, use `NunchakuQwenImageTransformer2DModel.set_offload(True, ...)` and exclude the transformer from Diffusers CPU offload. |
| Speed up long FLUX denoising | Apply First-Block Cache with `apply_cache_on_pipe(pipe, residual_diff_threshold=0.12)` or double FB cache thresholds. |
| Use Cache-DiT | Install `cache-dit`, then call `cache_dit.enable_cache(pipe, cache_config=DBCacheConfig(...))`; treat as optional dependency. |
| Try FP16 attention | On FLUX transformers, call `transformer.set_attention_impl("nunchaku-fp16")`; switch back with `"flashattn2"`. Turing needs FP16 attention. |
| Reduce T5 memory | Replace FLUX T5 with `NunchakuT5EncoderModel.from_pretrained(...)` and pass it as `text_encoder_2`; CUDA only and not currently for Turing. |
| Plan evidence-backed checks | Read `references/performance-controls.md#verification-planning` and treat native tests/examples as candidates, not pre-run evidence. |

## Architecture defaults

- **Turing / RTX 20-series / SM 75:** use INT4 weights, `torch.float16` for transformer and pipeline, `transformer.set_attention_impl("nunchaku-fp16")`, and offload if VRAM is tight. Do not select the quantized T5 encoder as a default because the docs state Turing support is pending.
- **Ampere / Ada / SM 80, 86, 89:** use INT4 weights, normally `torch.bfloat16`, default FlashAttention-2 unless comparing FP16 attention, and enable offload/qencoder/cache only when the task needs memory or speed trade-offs.
- **Blackwell / RTX 50-series / SM 120 or 121:** use FP4 weights, PyTorch >= 2.7, and CUDA >= 12.8; FP16 attention may be a speed candidate on 50-series.
- **Other GPU architectures or CPU-only:** Nunchaku's 4-bit CUDA kernels are not a full CPU workflow; report the unsupported backend instead of inventing CPU substitutes.

## Detailed references

- `references/performance-controls.md` — API fragments, thresholds, offload combinations, precision/device choices, and verification candidates.
- `references/troubleshooting.md` — CUDA/build mismatch, architecture, qencoder, cache/offload, and device-placement failure modes.
- `scripts/check_nunchaku_cuda.py` — safe JSON probe for installed runtime capabilities.
