---
name: cross-modal-generation
description: "Guides InternGPT ImageBind/StableUnCLIP audio, thermal, image,
  text generation and StyleGAN/DragGAN point editing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cross-Modal Generation

Use this sub-skill when a task asks for InternGPT generation or editing through ImageBind, StableUnCLIP, StyleGAN, or DragGAN: audio-to-image, thermal-to-image, audio+image-to-image, audio+text-to-image, "ImageBind", "StableUnCLIP", "DragGAN", "StyleGAN", "New Image", "click start/end points", or "Drag It".

## Route first

- For ImageBind/StableUnCLIP workflows, read [references/imagebind-workflows.md](references/imagebind-workflows.md) when you need tool names, input grammar, modality preprocessing, output naming, or sample-asset expectations.
- For StyleGAN and DragGAN point editing, read [references/draggan-workflows.md](references/draggan-workflows.md) when you need the app button sequence, state fields, point pairing rules, iteration behavior, or output artifacts.
- For common failures, read [references/troubleshooting.md](references/troubleshooting.md) when an ImageBind wrapper is missing, a comma input is malformed, assets are absent, CUDA/model downloads fail, VRAM is insufficient, or DragGAN points/checkpoints fail.
- Run [scripts/validate_multimodal_assets.py](scripts/validate_multimodal_assets.py) before invoking a multimodal tool when you need a safe local check for audio/image/thermal/video paths, extensions, and ImageBind comma-separated tool input grammar; it performs no model imports or downloads.

## Boundaries

- This sub-skill owns `Anything2Image`, `Audio2Image`, `Thermal2Image`, `AudioImage2Image`, `AudioText2Image`, `StyleGAN`, and DragGAN app-point workflows.
- Route general launch flags, model-zoo placement, Docker, HTTPS, OpenAI key, and broad `--load` planning to `../app-deployment/SKILL.md`.
- Route SAM, OCR, Husky, mask/inpainting, ControlNet, and general visual dialogue workflows to `../visual-dialogue-tools/SKILL.md`.
- Route video upload, video caption/action/dense caption, TikTok clip creation, ffmpeg, and Bark workflows to `../video-understanding/SKILL.md`.

## Operating cautions

Do not treat static validation as proof that full generation will run: actual ImageBind/StableUnCLIP and StyleGAN/DragGAN inference requires the runtime package stack, CUDA-capable PyTorch, large model checkpoints or model downloads, enough VRAM, and a configured app/service session. Prefer safe validators and references until the user explicitly asks to run the heavy runtime and confirms the environment is ready.
