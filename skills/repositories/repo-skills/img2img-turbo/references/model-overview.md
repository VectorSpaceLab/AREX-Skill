# Model Overview

## Purpose

Use this reference when deciding whether a task belongs to the paired Pix2Pix-Turbo route, the unpaired CycleGAN-Turbo route, or the training sub-skill.

## Two model families

| Family | Common selectors | Training mode | Input contract | Output contract | Route |
| --- | --- | --- | --- | --- | --- |
| Pix2Pix-Turbo | `edge_to_image`, `sketch_to_image_stochastic`, custom paired checkpoint | Paired translation | RGB image or sketch plus prompt; optional Canny thresholds, `gamma`, and `seed` depending on branch | One generated RGB image, saved under the input basename | [paired-inference](../sub-skills/paired-inference/SKILL.md) |
| CycleGAN-Turbo | `day_to_night`, `night_to_day`, `clear_to_rainy`, `rainy_to_clear`, custom unpaired checkpoint | Unpaired translation | RGB image plus built-in pretrained caption/direction or custom prompt + `a2b`/`b2a` | One generated RGB image, saved under the input basename | [unpaired-inference](../sub-skills/unpaired-inference/SKILL.md) |

## Shared runtime facts

- Both model families are built on Stable Diffusion Turbo components loaded through `diffusers`, `transformers`, and `peft`.
- Source inference code moves tensors and model components to CUDA.
- The paired branch can save a Canny preview and uses `canny_from_pil` for edge control.
- The unpaired branch uses an image-preparation transform and fixed prompt strings for pretrained modes.
- The training code writes checkpoints as `model_<step>.pkl` files.

## Checkpoint expectations

### Paired custom checkpoints

The paired model's `save_model()` path writes a state dict containing:

- `unet_lora_target_modules`
- `vae_lora_target_modules`
- `rank_unet`
- `rank_vae`
- `state_dict_unet`
- `state_dict_vae`

Use this route for paired custom checkpoints produced by the paired training workflow.

### Unpaired custom checkpoints

The unpaired model loader expects a custom checkpoint with separate unpaired weights and fixed prompts. When using `--model_path`, always provide both `--prompt` and `--direction`.

## Utility functions you will see again

- `image_prep.canny_from_pil`: builds the edge control image for paired edge-to-image inference.
- `my_utils.training_utils.build_transform`: shared image-preparation strings for inference and training.
- `model.make_1step_sched`: constructs the one-step scheduler shared by both model families.

## Route reminder

If the task is about command construction, safe validation, dataset layout, or troubleshooting for a specific family, go to the matching sub-skill instead of using this overview as a manual.
