---
name: image-and-face-apps
description: "Use PaddleGAN ppgan.apps image and face application predictors for
  single-image generation, restoration, denoising, super-resolution, style
  transfer, face parsing, enhancement, cartoonization, makeup transfer, and
  StyleGANv2 latent workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# image-and-face-apps

Use this sub-skill when the request stays in one image, one face, or one latent code at a time.

## Route here
- photo-to-anime and portrait cartoonization
- face parsing, face enhancement, and makeup transfer
- single-image denoising, deblurring, inpainting, super-resolution, and depth
- StyleGANv2 sampling, fitting, mixing, and editing
- Pixel2Style2Pixel inversion and SinGAN-style single-image generation

## Do not route here
- video restoration, motion driving, or lip-sync -> `video-and-audio-apps`
- exported or static inference model workflows -> `deployment-export`
- dataset download or preprocessing work -> `data-preparation`
- full runs without explicit weights, media, and backend approval

## Start with
1. Run `python scripts/check_image_app_deps.py` for a safe import/dependency check.
2. Open `references/image-workflows.md` to pick the right model family.
3. Open `references/predictor-api.md` for constructor and `run()` shapes.
4. Open `references/troubleshooting.md` when weights, dlib, CLIP, or face detection are missing.

## Output rule
Use a caller-owned output directory and keep file names predictable. Prefer explicit `weight_path` values when reproducibility or offline use matters.

## Notes
- Use installed `ppgan` package imports and bundled helpers, not source-checkout scripts.
- If a predictor can auto-download weights, say so before relying on that behavior.
- CLIP-guided StyleGAN editing is optional and not the default route here.
