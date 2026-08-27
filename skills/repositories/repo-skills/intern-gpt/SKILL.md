---
name: intern-gpt
description: "Operate InternGPT/InternChat multimodal agent deployments,
  visual-dialogue tools, cross-modal generation, DragGAN, and video workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# InternGPT

Use this skill when the task names InternGPT, InternChat, iGPT, iChat, or describes a pointing-language multimodal ChatGPT/Gradio agent that uses visual tools for image, audio, thermal, DragGAN, or video workflows.

Do not use this skill for unrelated Gradio, Stable Diffusion, SAM, ImageBind, or video-model tasks unless the user is working with InternGPT's `app.py` service, tool class names, `model_zoo` layout, Gradio tabs, or generated `image/` media workflow.

## First decisions

1. Identify the user's surface: service launch, image dialogue/masks, cross-modal generation/DragGAN, or video understanding.
2. Check whether the answer needs a live runtime or only a static plan. Most full InternGPT workflows need Linux, Python 3.8+, CUDA/PyTorch, large checkpoints in `model_zoo`, and sometimes an OpenAI API key.
3. Prefer the bundled static validators before recommending expensive launches or model calls.
4. Never claim a model output, Gradio service start, checkpoint conversion, Docker build, or OpenAI-backed clip generation unless that action was actually run in the user's provisioned environment.

## Route map

- Read [sub-skills/app-deployment/SKILL.md](sub-skills/app-deployment/SKILL.md) for install, `model_zoo`, OpenAI/HTTPS, `app.py` flags, `--load` strings, tabs, e-mode, and Docker GPU deployment.
- Read [sub-skills/visual-dialogue-tools/SKILL.md](sub-skills/visual-dialogue-tools/SKILL.md) for image upload state, click masks, OCR, SAM, Husky VQA/captioning, inpainting/removal/replacement, and ControlNet/Stable Diffusion image tools.
- Read [sub-skills/cross-modal-generation/SKILL.md](sub-skills/cross-modal-generation/SKILL.md) for ImageBind/StableUnCLIP audio, thermal, audio+image, audio+text generation and StyleGAN/DragGAN point editing.
- Read [sub-skills/video-understanding/SKILL.md](sub-skills/video-understanding/SKILL.md) for video upload, Tag2Text captions, InternVideo action recognition, GRiT dense captions, and TikTok-style clip generation.

## Shared references and scripts

- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, CUDA, checkpoint, credential, path, Docker, and validation failures before diving into workflow-specific troubleshooting.
- Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill is stale relative to a different InternGPT checkout.
- Read [references/repo-routing-metadata.json](references/repo-routing-metadata.json) for the structured managed repo-skill routing metadata.
- Run [scripts/check_static_skill_readiness.py](scripts/check_static_skill_readiness.py) from this skill directory after editing or before import/export to check required frontmatter, links, routing metadata, script syntax, and obvious path leaks.

## Installation snapshot

- Use this distilled setup baseline: create a Python 3.8+ environment, install the runtime requirements with `pip install -r requirements.txt`, and then add the model-zoo and checkpoint files needed for the workflow you want.
- If you only need to sanity-check the generated skill tree itself, run [scripts/check_static_skill_readiness.py](scripts/check_static_skill_readiness.py) first. That command is the minimal verification step for the generated skill package structure.

## Safe static checks

From this skill directory, use these checks before heavy runtime work:

```bash
python scripts/check_static_skill_readiness.py --skill-root .
python sub-skills/app-deployment/scripts/validate_load_plan.py --load "StyleGAN_cuda:0" --tab DragGAN --https -e
python sub-skills/cross-modal-generation/scripts/validate_multimodal_assets.py --tool AudioText2Image --tool-input "sample.wav,a rainy street"
python sub-skills/video-understanding/scripts/validate_video_plan.py --video sample.mp4 --tool ActionRecognition --uniformerv2-ready
```

For mask workflows, use [sub-skills/visual-dialogue-tools/scripts/validate_mask_inputs.py](sub-skills/visual-dialogue-tools/scripts/validate_mask_inputs.py) with real local image and mask paths. That helper needs Pillow because it verifies readable image dimensions and non-empty mask pixels.

## Runtime boundary

InternGPT is not packaged as a normal importable distribution in this checkout. Treat it as a service-style repository launched through its app entry point after dependency and checkpoint preparation. Static validators in this skill intentionally avoid importing InternGPT modules because those imports can pull heavy model stacks, download checkpoints, require credentials, or start services.
