---
name: inference
description: "Run ICEdit single-image editing from the CLI, including normal
  LoRA inference, MoE inference, prompt templating, image-width normalization,
  output saving, seed control, and CPU-offload guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inference

Use this sub-skill for one-image, prompt-driven editing in the command line.

- Normal LoRA editing and MoE LoRA editing through one bundled helper.
- Normal mode is standalone; default model ids resolve through the Hub and weights are not bundled.
- The fixed diptych prompt template the helper prepends automatically.
- 512-pixel width normalization, height rescaling, and output naming.
- Model and LoRA selection, seed control, and `--enable-model-cpu-offload`.
- MoE mode requires an ICEdit checkout with vendored `icedit/`, passed via `--repo-root`.

## What it does not cover
- browser or Gradio launch details; use the root `ic-edit` skill and its `gradio` route
- training launch, configs, and dataset prep; use the root `ic-edit` skill and its `training` route

## Bundled files
- `scripts/run_icedit_inference.py`: one helper for both `--mode normal` and `--mode moe`
- `references/quickstart.md`: command templates and mode selection
- `references/examples.md`: bundled example images and width-normalization notes
- `references/troubleshooting.md`: common failure modes and fixes

## Fast route
1. Pick `--mode normal` for standalone standard LoRA inference or `--mode moe` only with a checkout that contains `icedit/`.
2. Set `--image` and `--instruction`; the helper prepends the fixed prompt template for you.
3. Override `--flux-path` and `--lora-path` when you want local weights instead of Hub ids.
4. Add `--enable-model-cpu-offload` on lower-VRAM CUDA machines.
5. Read `references/troubleshooting.md` if CUDA, download, resize, or seed behavior looks off.
