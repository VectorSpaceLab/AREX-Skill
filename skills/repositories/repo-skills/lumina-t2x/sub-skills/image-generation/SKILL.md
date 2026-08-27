---
name: image-generation
description: "Routes Lumina-T2I, Lumina-Next-T2I, mini, compositional,
  checkpoint-conversion, demo, and img2img/SD3 image-generation tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Image Generation

Use this subskill for text-to-image inference and related demo/setup tasks across the Lumina image branches.
It covers the `lumina` and `lumina_next` console scripts, the `demo.py` and `sample.py` entry points, compositional image generation, checkpoint conversion, and the simplified mini/img2img/SD3 inference paths.

## Include here

- Lumina-T2I image inference from a checkpoint directory.
- Lumina-Next-T2I image inference, including the console `lumina_next infer` route.
- Checkpoint conversion between `.pth` and `.safetensors` for image models.
- Lumina-Next-T2I-Mini inference, img2img, and SD3 image generation.
- Compositional image generation with multiple captions per region.
- Demo launch and prompt/resolution configuration for image generation.

## Exclude or route elsewhere

- Training, finetuning, or DreamBooth-style adaptation: use `image-training`.
- Audio or music generation: use `audio-music`.
- Visual anagrams and illusion animation: use `visual-anagrams`.
- ImageNet benchmark training: use `imagenet-training`.

## Read first

- `references/workflows.md` for the supported image-generation commands and checkpoint layouts.
- `references/troubleshooting.md` for the shared image backend and checkpoint failures.
- `scripts/check_checkpoints.py` before launching inference if the checkpoint tree is uncertain.

## Fast routing hints

- If the user says `lumina infer` or `lumina convert`, stay in this subskill.
- If the user says `lumina_next infer`, `sample.py`, `img2img`, `compositional generation`, or `SD3`, stay in this subskill.
- If the user asks about training, resume, `torchrun`, or `JourneyDB`, hand off to `image-training`.
