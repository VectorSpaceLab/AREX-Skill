---
name: image-upscaling
description: "Guides QualityScaler still-image upscaling, tiling, blending,
  metadata copy, and output naming."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# image-upscaling

Use this sub-skill when the task is about upscaling photos or other still images, reasoning about the AI image core, previewing image output names, or troubleshooting image-specific channel and tiling behavior.

## Read this when

- The user wants to upscale a photo or still image.
- The task asks about model choice, alpha handling, grayscale handling, or tiling.
- You need to explain the image output filename pattern.
- Metadata copy or blending behavior is relevant.
- The runtime is ready, but the image pipeline still misbehaves.

## What this sub-skill owns

- `AI_upscale` and the still-image path through `AI_orchestration`.
- Image preprocessing, normalization, postprocessing, and resizing.
- Tiling decisions and tile-combination behavior.
- Image output naming, extension selection, and blending.
- Metadata copy from source image to output image.

## What belongs elsewhere

- Launch, install, provider, and asset readiness belong in `setup-runtime`.
- Video frame extraction, resume, and encoding belong in `video-upscaling`.
- Shared model names, output suffix rules, and supported formats live in the root references.

## Core workflow

1. Read `references/ai-core-and-image-flow.md` for the verified image pipeline.
2. Read `references/image-tiling-and-format-matrix.md` for the model, format, and tile matrix.
3. Read `references/image-failure-modes.md` if output colors, alpha handling, or edge pixels look wrong.
4. Use `../../scripts/derive_qualityscaler_paths.py` to preview image output names.

## Important facts

- The image pipeline lazily creates the ONNX session and uses the selected model file.
- The input image may be RGB, RGBA, or grayscale.
- Large images are tiled once they exceed the tile-pixel threshold.
- Output names are built from the input stem plus model, resize, and blending suffixes.
- Metadata copy is best-effort; a metadata failure does not necessarily mean the image write failed.

## Common user intents

- "What happens to alpha channels?" -> read the image flow reference.
- "Why are the corners missing?" -> inspect the tiling reference and the tile-edge limitation.
- "What file will this image produce?" -> run the path helper or read the output contract reference.
- "Why did metadata not copy?" -> read the failure modes page and check for `exiftool.exe`.

## Bundled references

- `references/ai-core-and-image-flow.md`
- `references/image-tiling-and-format-matrix.md`
- `references/image-failure-modes.md`

## Bundled scripts

- `../../scripts/derive_qualityscaler_paths.py` for output-name previews.

## Stop conditions

If the problem is actually missing runtime support, a missing model file, or a GUI launch issue, route back to `setup-runtime` before debugging image logic.
