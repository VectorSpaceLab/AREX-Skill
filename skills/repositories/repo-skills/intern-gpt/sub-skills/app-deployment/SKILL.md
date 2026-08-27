---
name: app-deployment
description: "Install, configure, launch, and sanity-check InternGPT/InternChat services."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# app-deployment

Use this sub-skill when the task is to install, configure, launch, containerize, or sanity-check an InternGPT/InternChat Gradio service. It owns app-level CLI planning, model-zoo placement, HTTPS/OpenAI setup, Docker GPU deployment, and static validation of `--load`/`--tab` choices.

Route detailed workflow questions elsewhere:

- Read [../visual-dialogue-tools/SKILL.md](../visual-dialogue-tools/SKILL.md) for detailed image, mask, OCR, SAM, Husky VQA, inpainting, and image-tool behavior after the service is running.
- Read [../cross-modal-generation/SKILL.md](../cross-modal-generation/SKILL.md) for detailed ImageBind audio/thermal/image-conditioned generation and DragGAN point-editing usage.
- Read [../video-understanding/SKILL.md](../video-understanding/SKILL.md) for detailed video caption/action/dense-caption/TikTok workflows.

## Deployment routing

- For CLI flags, supported `--load` classes, tab names, and launch-plan sanity checks, read [references/cli-and-config.md](references/cli-and-config.md).
- For `model_zoo/`, checkpoints, Husky/LLaMA conversion, SAM, LaMa, Tag2Text, GRiT, StyleGAN, ImageBind, and StableUnCLIP prerequisites, read [references/model-zoo.md](references/model-zoo.md).
- For basic, full, DragGAN-only, HTTPS, OpenAI, and Docker GPU launch recipes, read [references/deployment-recipes.md](references/deployment-recipes.md).
- For common failures such as missing `model_zoo`, bad LLaMA/Husky partial conversion, missing OpenAI key, `OPENAI_API_BASE`, certificate errors, CUDA/VRAM mismatch, Docker placeholder volumes, detectron2/OpenCV pitfalls, and `-e` expectations, read [references/troubleshooting.md](references/troubleshooting.md).
- Run [scripts/validate_load_plan.py](scripts/validate_load_plan.py) before recommending a launch command or compose command when the user asks which `--load` or `--tab` string to use.

## Quick decision guide

1. Choose the smallest tab set that matches the user's task: `DragGAN` for StyleGAN point editing, `Image` for image upload/click/OCR/segmentation/dialogue, `Audio` for ImageBind audio input, and `Video` for video upload/analysis.
2. Choose the smallest direct `--load` list that provides those tabs' tools; template tools are auto-created only after their prerequisites load.
3. Prefer `-e`/`--e-mode` for constrained VRAM, but do not describe it as CPU-only: the app still expects CUDA for normal launches, and the speech model is initialized on `cuda:0`.
4. Check `model_zoo/`, `certificate/`, and OpenAI configuration before treating a launch failure as a Python bug.
5. For Docker, replace every placeholder volume with real host directories and keep GPU reservation/container-toolkit requirements explicit.

## Safe default recipes

- Basic image-dialogue service: `HuskyVQA_cuda:0,SegmentAnything_cuda:0,ImageOCRRecognition_cuda:0` with `-e` on a CUDA machine and a populated `model_zoo/`.
- Low-memory DragGAN-only HTTPS service: `StyleGAN_cuda:0`, `--tab DragGAN`, `--https`, and `-e`, plus `certificate/cert.pem`, `certificate/key.pem`, and StyleGAN checkpoint readiness.
- Full multimodal demo: use the long full-feature load string in `references/deployment-recipes.md`; warn that it is heavy and requires multiple model families, CUDA, and usually far more setup than a task-specific launch.
