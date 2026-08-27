# Model and Asset Reference

## Purpose

Read this when choosing model ids, local weights, or example inputs for ICEdit.

## Core model ids

| Item | Used by | Notes |
| --- | --- | --- |
| `black-forest-labs/flux.1-fill-dev` | normal inference and normal Gradio demo | Default base model id for the shipped helpers |
| `RiverZ/normal-lora` | normal inference and normal Gradio demo | Default normal LoRA weight id |
| `sanaka87/ICEdit-MoE-LoRA` | MoE inference and MoE Gradio demo | Default MoE LoRA weight id |

## Optional low-VRAM assets

These files are user-provided; model weights and GGUF files are not bundled in the skill.

| Item | Used by | Notes |
| --- | --- | --- |
| `FLUX.1-Fill-dev-gguf` transformer file | Gradio demo | Pass an existing local file through `--transformer` when using GGUF quantization |
| `t5-v1_1-xxl-encoder-gguf` text encoder file | Gradio demo | Pass an existing local file through `--text-encoder-2` / `--text_encoder_2` |
| `sub-skills/gradio/scripts/config.json` | Gradio helper | Bundled FluxTransformer2DModel config used for GGUF loading; it is not the model file |

If a local checkpoint, LoRA, or GGUF path is missing, the helper fails before execution; omit optional GGUF flags to use the normal path or fix the path. Hub ids require network access/cache and authentication where applicable.

## Input-image rule

- The editing helpers expect a source image width of 512 pixels.
- If the width differs, the helper resizes it to width 512 and rounds the new height down to a multiple of 8.
- The helper does not expose a separate width override because the input image controls the geometry.

## Bundled example images

| Image | Why it is useful |
| --- | --- |
| `sub-skills/inference/references/assets/girl.png` | Clean starter image for CLI editing smoke checks |
| `sub-skills/inference/references/assets/boy.png` | Another width-512 example for prompt edits |
| `sub-skills/inference/references/assets/kaori.jpg` | Exercises the automatic resize-to-512 path |

The Gradio route bundles the same trio under `sub-skills/gradio/references/examples/` with matching prompts and seeds.

## Model-selection guidance

- Use the normal LoRA id when you want the simplest supported path.
- Use the MoE id only when you have a checkout that includes the vendored `icedit/` package and you explicitly want the MoE route.
- Add CPU offload only when the CUDA GPU is too small for the full model path; it is slower than the full-GPU route.
