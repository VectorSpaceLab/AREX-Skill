---
name: flux-pipelines
description: "Operate Nunchaku FLUX and FLUX v2 Diffusers replacement workflows
  for text-to-image, Kontext editing, and FLUX.1 tools."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# flux-pipelines

Use this operating sub-skill when a task asks to replace a Diffusers FLUX transformer with Nunchaku quantized FLUX weights, including basic FLUX.1-dev, FLUX.1-schnell, FLUX.1-krea-dev, FLUX.1-Kontext-dev, and FLUX.1 Tools-style Canny/Depth/Fill/Redux/ControlNet routes.

## Fast route

1. Pick the Diffusers pipeline class from the task:
   - Text-to-image FLUX.1-dev, schnell, and krea: `diffusers.FluxPipeline`.
   - Kontext image editing: `diffusers.FluxKontextPipeline` with an input `image=`.
   - Canny or Depth control: `diffusers.FluxControlPipeline` with `control_image=`.
   - Fill/inpaint: `diffusers.FluxFillPipeline` with `image=` and `mask_image=`.
   - Redux: `diffusers.FluxPriorReduxPipeline` first, then a `FluxPipeline` using the prior output.
2. Load the Nunchaku transformer from a Hugging Face model-file path or local quantized asset path:
   - Current/legacy examples: `NunchakuFluxTransformer2dModel.from_pretrained(transformer_path, torch_dtype=..., offload=...)`.
   - FLUX v2 examples: `NunchakuFluxTransformer2DModelV2.from_pretrained(transformer_path, torch_dtype=..., device=...)`.
3. Pass the loaded transformer into `PipelineClass.from_pretrained(base_model, transformer=transformer, torch_dtype=...)`.
4. Use CUDA by default. Use `torch.bfloat16` on Ampere/Ada/Hopper/Blackwell unless the task or GPU requires FP16. On Turing GPUs use `torch.float16`, call `transformer.set_attention_impl("nunchaku-fp16")` when available, and enable CPU offload if VRAM is tight.
5. Keep LoRA/adapters/cache/qencoder details out of this sub-skill; route those to sibling sub-skills for `lora-and-adapters` or `performance-and-memory`.

## Safe defaults

- Transformer asset: a single `.safetensors`/`.sft` path such as `nunchaku-tech/nunchaku-flux.1-dev/svdq-int4_r32-flux.1-dev.safetensors`, or a local path supplied by the user.
- Precision selection: prefer `nunchaku.utils.get_precision()` when constructing public examples; it returns `fp4` on Blackwell-class devices and `int4` otherwise.
- Device: `cuda` unless the caller explicitly asks for a device id such as `cuda:1`.
- Offload: for `NunchakuFluxTransformer2dModel`, `offload=True` can be passed to transformer loading and paired with Diffusers sequential CPU offload. For `NunchakuFluxTransformer2DModelV2`, source inspection shows `from_pretrained(..., offload=True)` raises `NotImplementedError`; rely on Diffusers pipeline offload or choose the non-V2 class when transformer-level offload is required.
- Metadata: only the non-V2 `NunchakuFluxTransformer2dModel.from_pretrained(..., return_metadata=True)` path is documented in source as returning `(transformer, metadata)`. Always unpack it explicitly and tolerate `metadata is None` for legacy directory-style loading.

## Bundled files

- `references/flux-workflows.md` — model-family routing table, class choices, example call patterns, and API caveats.
- `references/troubleshooting.md` — common loading, dtype/device/offload, Turing, model access, and CUDA failure diagnoses.
- `scripts/flux_minimal_template.py` — parameterized one-image FLUX template for installed `nunchaku` environments.

## Minimal command template

```bash
python scripts/flux_minimal_template.py \
  --transformer nunchaku-tech/nunchaku-flux.1-dev/svdq-int4_r32-flux.1-dev.safetensors \
  --base-model black-forest-labs/FLUX.1-dev \
  --prompt "A cat holding a sign that says hello world" \
  --output flux-output.png \
  --dtype bf16 \
  --device cuda
```

This command requires accessible model assets, a CUDA-capable Nunchaku installation, Diffusers, and any Hugging Face credentials required by the selected base or transformer models.

## Verification candidates, not pre-run checks

Native source candidates for a verifier include `tests/flux/test_flux_examples.py`, selected `tests/v1/flux/test_flux1_*.py` cases, and representative `examples/flux*.py` or `examples/v1/flux*.py` scripts. Treat them as candidates only; this sub-skill was drafted without running repository-native tests, examples, or benchmarks.
