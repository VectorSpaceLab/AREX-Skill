---
name: sana-zimage-sdxl
description: "Operate Nunchaku's non-FLUX Diffusers replacements for Sana,
  Z-Image, SDXL, and SDXL-Turbo."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# sana-zimage-sdxl

Use this sub-skill when a task needs Nunchaku's non-FLUX image-generation replacements:

- `NunchakuSanaTransformer2DModel` with `SanaPipeline` or `SanaPAGPipeline`.
- `NunchakuZImageTransformer2DModel` with `ZImagePipeline`.
- `NunchakuSDXLUNet2DConditionModel` with `StableDiffusionXLPipeline` for SDXL or SDXL-Turbo.

Do **not** use this sub-skill for FLUX, Qwen-Image, LoRA/adapters, or performance-cache/offload tuning beyond the family-specific notes here. Do not claim CPU-only inference support: Nunchaku quantized inference requires a compatible CUDA backend even when Diffusers sequential CPU offload is used for memory placement.

## Route by family

| User intent | Use | Read next |
| --- | --- | --- |
| Sana 1.6B text-to-image | `NunchakuSanaTransformer2DModel.from_pretrained(...)` then `SanaPipeline.from_pretrained(..., transformer=...)` | `references/non-flux-models.md#sana` |
| Sana with PAG | Same Sana transformer, pass `pag_layers`, then `SanaPAGPipeline` with matching `pag_applied_layers` | `references/non-flux-models.md#sana-pag` |
| Z-Image-Turbo | `NunchakuZImageTransformer2DModel.from_pretrained(...)` then `ZImagePipeline.from_pretrained(..., transformer=...)` | `references/non-flux-models.md#z-image-turbo` |
| SDXL base | `NunchakuSDXLUNet2DConditionModel.from_pretrained(...)` then `StableDiffusionXLPipeline(..., unet=...)` | `references/non-flux-models.md#sdxl-and-sdxl-turbo` |
| SDXL-Turbo | Same SDXL UNet class with the SDXL-Turbo quantized asset and base pipeline | `references/non-flux-models.md#sdxl-and-sdxl-turbo` |
| Failure, asset, precision, or backend issue | Diagnose family/class mismatch, CUDA support, safetensors, dtype, offload, or PAG setup | `references/troubleshooting.md` |

## Safe operating workflow

1. Identify the model family first; never swap a quantized Sana/Z-Image transformer into an SDXL UNet slot or vice versa.
2. Require the caller to provide both the Diffusers base model ID/path and the Nunchaku quantized `.safetensors`/`.sft` asset path. Avoid silent repo defaults.
3. Choose dtype/device from the target GPU: `torch.bfloat16` is the normal Ampere/Ada path; Z-Image uses `torch.float16` on Turing GPUs. Sana and SDXL native candidates skip Turing and FP4 paths.
4. Construct the Diffusers pipeline by passing the Nunchaku replacement component at `from_pretrained` time, then move or offload the pipeline according to the family notes.
5. Run a bounded smoke generation only when model assets, credentials, CUDA, and output budget are explicitly available.

## Bundled template

Use `scripts/non_flux_template.py` as a parameterized starter. It supports `--family sana|zimage|sdxl`, requires explicit `--base-model` and `--quantized-path`, and fails clearly for missing local assets or unsupported family/variant combinations.

## Verification candidates

The following native tests/examples are evidence and future verification candidates only; this skill does not claim they were run:

- `examples/sana1.6b.py`, `examples/sana1.6b_pag.py`, `tests/sana/test_examples.py`
- `examples/v1/z-image-turbo.py`, `tests/v1/z_image/test_z_image_turbo.py`
- `examples/v1/sdxl.py`, `examples/v1/sdxl-turbo.py`, `tests/v1/sdxl/test_sdxl.py`
