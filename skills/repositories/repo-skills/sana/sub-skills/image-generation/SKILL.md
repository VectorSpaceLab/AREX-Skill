---
name: image-generation
description: "Plan and troubleshoot Sana image generation workflows across
  Diffusers, native pipelines, Sprint, ControlNet, high-resolution tiling,
  quantization, and Gradio launch modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sana Image Generation

Use this sub-skill when a user wants to generate or troubleshoot still images
with Sana, Sana-1.5, SANA-Sprint, Sana ControlNet HED, Diffusers Sana pipelines,
4-bit/8-bit quantized inference, 2K/4K high-resolution generation, prompt-file
batch inference, or Gradio image demos.

This sub-skill is for planning and operating image inference workflows. It does
not own training/data conversion, benchmark metrics, checkpoint conversion,
SGLang/ComfyUI deployment, video generation, world models, or streaming.

## Fast Route

1. **Choose the execution surface.**
   - For common text-to-image use in Python, prefer Diffusers
     `SanaPipeline`, `SanaPAGPipeline`, or `SanaSprintPipeline`; read
     [diffusers-and-quantization.md](references/diffusers-and-quantization.md).
   - For repository-native `.pth` checkpoints, config YAMLs, batch prompt
     files, or ControlNet HED JSON inputs, read
     [native-image-workflows.md](references/native-image-workflows.md).
   - For model IDs, native checkpoint/config pairing, resolution, precision,
     and 2K/4K selection, read
     [model-config-selection.md](references/model-config-selection.md).
   - For CUDA, Hugging Face, dtype, OOM, prompt file, ControlNet, xformers,
     flash-attn, or Gradio failures, read
     [troubleshooting.md](references/troubleshooting.md).
2. **Use a safe helper before running expensive generation.**
   - `scripts/plan_sana_image_command.py` prints a native command or Diffusers
     snippet and warnings without loading models or starting servers.
   - `scripts/validate_controlnet_request.py` checks a ControlNet JSON and
     reference images/control maps without running the model or annotator.
3. **Validate outputs after the real run.** Check that the output directory
   exists, at least one `.jpg`/`.png` file was written, images open with PIL,
   and sizes match the requested or aspect-ratio-binned resolution.

## Decision Checklist

- **Need lowest friction?** Use Diffusers with a `*_diffusers` model id and a
  matching `variant`/`torch_dtype` pair.
- **Need PAG guidance?** Use `SanaPAGPipeline` or native `pag_scale > 1` with a
  linear-attention config; otherwise guidance falls back to classifier-free.
- **Need one/few-step speed?** Use SANA-Sprint with `SanaSprintPipeline`, the
  Sprint `.pth` checkpoint/config pair, `sampling_algo=scm`, and usually two
  steps.
- **Need edge/sketch conditioning?** Use Sana ControlNet HED. Validate that each
  JSON item has a prompt and exactly one of `ref_image_path` or
  `ref_controlmap_path`; HED preprocessing requires a CUDA annotator checkpoint.
- **Need 2K/4K?** Use the 2K/4K bf16 model IDs/configs, enable VAE tiling for
  4K, and plan for high VRAM. Do not claim CPU fallback for generation.
- **Need low VRAM?** Prefer 4-bit SVDQuant/Nunchaku for image inference when
  the Nunchaku engine is installed; use 8-bit bitsandbytes for Diffusers
  component quantization when quality and dependency trade-offs are acceptable.

## Safe Command Planning Examples

Print a Diffusers PAG snippet:

```bash
python scripts/plan_sana_image_command.py \
  --mode diffusers \
  --diffusers-pipeline pag \
  --model-family sana15 \
  --prompt 'a cyberpunk cat with a neon sign that says "Sana"' \
  --seed 42
```

Print a native batch command for a prompt text file:

```bash
python scripts/plan_sana_image_command.py \
  --mode native \
  --native-workflow sana \
  --resolution 1024 \
  --prompt-file prompts.txt \
  --work-dir output/sana-run \
  --sample-nums 10
```

Check a ControlNet request before running generation:

```bash
python scripts/validate_controlnet_request.py \
  --json-file controlnet_request.json \
  --config configs/sana_controlnet_config/Sana_1600M_1024px_controlnet_bf16.yaml
```

## Boundaries

- Route training, image/text data layout, WebDataset/WIDS conversion,
  LoRA/DreamBooth, FSDP/DDP, or Sprint training to `training-data-configs`.
- Route metrics, checkpoint conversion/export, SVDQuant conversion, SGLang,
  ComfyUI, or broad deployment to `evaluation-conversion-deployment`.
- Route video, SANA-WM, LongSANA, or streaming V2V to `video-world-streaming`.

## Evidence Labels

This sub-skill was distilled from the Sana README, installation/model-zoo/image
inference/Sprint/ControlNet/4-bit/8-bit docs; native app pipeline classes; image
inference scripts; ControlNet utility code; and config families under
`configs/sana_config`, `configs/sana1-5_config`, `configs/sana_sprint_config`,
`configs/sana_controlnet_config`, and `configs/sana_app_config`. These are
provenance labels only; the operating guidance above is self-contained.
