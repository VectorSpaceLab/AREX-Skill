---
name: training-and-postprocessing
description: "Use textual inversion and hypernetwork create/train endpoints,
  plan preprocessing for training datasets, and operate Stable Diffusion WebUI
  extras/postprocessing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Training and Postprocessing

Use this sub-skill when the task mentions textual inversion, hypernetwork training, creating embeddings/hypernetworks, preprocessing training images, captioning/splitting/cropping datasets, extras upscaling, face restoration, or postprocessing scripts.

## Route First

- Use `../assets-and-models/SKILL.md` for embedding/hypernetwork/checkpoint placement, model discovery, refresh lists, and missing asset folders.
- Use `../api-automation/SKILL.md` for API server startup, authentication, request transport, base64 image encoding/decoding, and polling mechanics.
- Use `../launch-and-config/SKILL.md` for launch flags, low VRAM setup, CUDA/device flags, and server process lifecycle.
- Use `../extension-scripting/SKILL.md` for authoring custom scripts or extensions beyond built-in postprocessing controls.

## What This Covers

- Training endpoints: `/sdapi/v1/create/embedding`, `/sdapi/v1/train/embedding`, `/sdapi/v1/create/hypernetwork`, `/sdapi/v1/train/hypernetwork`.
- Training inputs: templates, dataset directory layout, captions, width/height, learning-rate strings, save/preview intervals, latent sampling, tag shuffle/dropout, and interrupt behavior.
- Preprocessing-for-training: split oversized images, auto focal crop, auto-sized crop, flipped copies, captioning, and safe validation of preprocessing plans.
- Extras/postprocessing: `/sdapi/v1/extra-single-image`, `/sdapi/v1/extra-batch-images`, built-in Upscale, GFPGAN, CodeFormer, PNG info/caption side effects, and image utility workflows.

## Core Workflow

1. Classify the request as training, preprocessing, extras/postprocessing, or troubleshooting.
2. Read [training-reference.md](references/training-reference.md) for endpoint names, payload fields, template expectations, validation order, and long-run safeguards.
3. For dataset preprocessing, draft a JSON plan and run [validate_preprocess_plan.py](scripts/validate_preprocess_plan.py) before any image/model work.
4. Read [postprocessing-reference.md](references/postprocessing-reference.md) for extras payload fields, postprocessing script names, ordering, upscaler/face-restorer checks, and output behavior.
5. Use [troubleshooting.md](references/troubleshooting.md) when an endpoint returns an `info` string with `error:`, skips images, fails to find templates/assets, or appears stuck.

## Safe Plan Validator

Validate a preprocessing plan without importing image, model, or WebUI modules:

```bash
python scripts/validate_preprocess_plan.py plan.json
```

The script accepts JSON with `source_dir`, `output_dir`, optional `target_width`/`target_height`, and an `operations` list containing objects such as `split_oversized`, `autosized_crop`, `focal_crop`, `create_flipped_copies`, `caption`, `upscale`, and `face_restoration`. It reports blocking errors, long-run/model prerequisites, and warnings about risky overwrites or expensive operations.

## Success Signals

- Training create endpoints return `info` containing the created file path; train endpoints return `info` containing `complete`, `filename`, and `error: None`.
- Training validates the selected model name, non-empty learning rate, positive integer batch/gradient/steps, existing non-empty dataset directory, selected template file, and log directory when saving previews/checkpoints.
- Extras endpoints return HTTP 200 with generated image(s) or HTML info when enabled; upscaler and face restoration names must be available from the running WebUI.
- Preprocessing plans validate cleanly before long-running operations and make output/overwrite behavior explicit.
