---
name: model-utilities
description: "Use sd-scripts model and network utilities safely: LoRA
  merge/extract/resize/convert, checkpoint or Diffusers conversion, metadata
  inspection, ControlNet helpers, and image utility helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Utilities

Use this sub-skill when the task is about manipulating, inspecting, converting, or planning model/adapter utility workflows with sd-scripts. These workflows are powerful and often write large checkpoint files, so default to read-only inspection and explicit planning before invoking destructive scripts.

## Route First

- Use `../training` for training command selection, optimizer/network choices, and resume/save strategy.
- Use `../generation` for image generation, prompt sampling, and inference pipeline use.
- Use `../data-preparation` for dataset validation, captioning, bucketing, or cache setup unless the user specifically asks for an image utility such as canny edges or face-rotation crops.
- Stay here for LoRA/network merge, extract, resize, conversion, metadata inspection, checkpoint/Diffusers conversion, SD3/FLUX component merging, ControlNet helper planning, and small image utility helpers.

## Safe Operating Rules

1. Identify the source family before planning: SD1/SD2, SDXL, SD3, FLUX, Hunyuan Image, Anima, Diffusers directory, `.ckpt`, or `.safetensors`.
2. Treat merge, extract, resize, and conversion scripts as checkpoint writers. Confirm output paths, free disk space, precision, device, and backups before running them.
3. Never reuse an input model path as an output path. Prefer a new output directory and an atomic-looking filename that records family, operation, precision, and date/version.
4. Validate model counts against ratio counts before LoRA or checkpoint merges. For LoRA merge scripts, `--models` and `--ratios` must align one-to-one.
5. Prefer CPU for planning and metadata inspection. Use GPU only when the selected utility needs it and the user accepts memory pressure.
6. For quick safe inspection, use the bundled script:

```bash
python skills/sd-scripts/sub-skills/model-utilities/scripts/inspect_safetensors_metadata.py MODEL.safetensors --include-keys --max-keys 20
```

## Common Workflows

- **Metadata inspection:** Use the bundled read-only helper for `.safetensors` headers. It does not load tensor payloads and is safer than conversion utilities.
- **LoRA merge:** Select the family-specific merge workflow for SD1/SD2, SDXL, or FLUX. Check model family, dimensions, alphas, ratio count, and output path first.
- **LoRA extraction:** Plan SD/SDXL or FLUX extraction separately. Extraction loads two large models and computes SVD; plan device, rank, precision, and memory.
- **LoRA resize/check:** Plan rank reduction, dynamic resizing, or tensor-stat inspection before replacing a production adapter.
- **Format conversion:** Confirm source and destination conventions before converting FLUX, Anima, or Hunyuan Image LoRA formats.
- **Checkpoint/Diffusers conversion:** Plan SD v1/v2 checkpoint/Diffusers conversion or FLUX Diffusers-to-safetensors conversion with explicit input/output format checks.
- **Model merging:** Treat safetensors checkpoint averaging and SD3 component assembly as large write operations that require backups and free disk checks.
- **Control/image helpers:** Plan edge-map generation, anime face crop/rotation, VAE-backed latent upscaling, or original ControlNet preprocessing only after confirming dependencies and output paths.

## References

- Start with `references/utility-catalog.md` to select the right utility family and route adjacent tasks.
- Use `references/conversion-and-merge-workflows.md` for safety checklists and command-planning templates.
- Use `references/troubleshooting.md` for format mismatch, missing metadata, ratio mismatch, overwrite risk, disk, memory, and family-specific failure modes.
