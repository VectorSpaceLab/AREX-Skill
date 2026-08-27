---
name: demos-and-watermarking
description: "Use and adapt generative-models demo UI routes and invisible
  watermark threshold logic safely without running heavyweight demo servers by
  default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Demos and Watermarking

Use this sub-skill when the user asks about Streamlit or Gradio demos, SDXL Turbo demo behavior, `video_sampling` UI settings, demo optional dependencies, converting demo controls into an API/script call, or interpreting invisible watermark bit-match counts.

## Start Here

- Treat demo files as UI reference material first. They import heavy libraries, may load CUDA models, may download checkpoints, and may bind local ports.
- For automated image generation, route SDXL text/image workflows to `../inference-api/SKILL.md` and translate UI controls into direct API arguments instead of launching Streamlit.
- For standalone SVD, SV3D, or SV4D command-line generation, route to `../video-sampling/SKILL.md`.
- For training, config authoring, or dataset setup, route to `../training-and-configs/SKILL.md`.
- For watermark-only questions, use `scripts/watermark_match_thresholds.py`; it mirrors the repository detector thresholds without importing `cv2`, `imwatermark`, or model code.

## Core References

- `references/demo-reference.md` maps the Streamlit/Gradio apps, modes, control names, output behavior, optional dependencies, and adaptation templates.
- `references/watermarking.md` explains the fixed 48-bit watermark, embed/detect relationship, bit-match thresholds, input expectations, and caveats.
- `references/troubleshooting.md` maps common demo and watermark symptoms to likely causes and recovery steps.
- `scripts/watermark_match_thresholds.py` classifies integer bit-match counts or JSON lists from another detector.

## Safe Workflow

1. Identify whether the user wants a UI explanation, a runnable automated generation path, or watermark interpretation.
2. If the request is automation, preserve the demo settings that matter and route to the API or video sub-skill rather than using the UI server.
3. If the user specifically wants a demo, list dependency/checkpoint/GPU/port prerequisites and ask before launching anything long-running or networked.
4. If the request is watermark detection, separate bit extraction from threshold interpretation: this skill classifies counts, while full image decoding still requires the original detector dependencies.

## Demo Setting Translation

When converting a UI interaction into non-UI code, capture these values explicitly:

- Text/image SDXL: model version, prompt, negative prompt if used, resolution, seed, sampler, step count, guidance settings, image-to-image strength, optional refiner version, and refinement strength.
- SDXL Turbo: prompt, seed, step count from 1 to 4, fixed 512x512 resolution, and Euler ancestral substep behavior.
- SVD/SV3D: version, input image path, height, width, frame count, fps, motion bucket, conditioning augmentation, decoding chunk size, camera elevation/trajectory for SV3D, and save path.
- Gradio SVD/SV4D: uploaded media, seed/randomization, motion/fps controls, encoding/decoding chunk sizes, denoising steps, and background-removal preference.

## Watermark Threshold Helper

Examples for already-extracted bit counts:

```bash
python sub-skills/demos-and-watermarking/scripts/watermark_match_thresholds.py 26 28 34 36 48
python sub-skills/demos-and-watermarking/scripts/watermark_match_thresholds.py --json '[26, 34, 36, 48]'
```

Use this helper only after another process has produced bit-match counts. It does not decode images and intentionally has no image-processing dependencies.
