---
name: media-processing
description: "Use MMCV image, video, optical-flow, visualization, and array
  quantization utilities safely without reopening MMCV source docs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMCV Media Processing

Use this sub-skill when a task asks for MMCV media utilities: reading or writing images, decoding image bytes, resizing, cropping, flipping, padding, rotating, normalizing or denormalizing arrays, color conversions, photometric helpers, converting tensors to images, reading or writing video/frames, ffmpeg-backed video edits, dense or sparse optical flow IO/quantization/warping, drawing boxes, converting flow to RGB, or scalar array quantization.

## Read First

- `references/api-reference.md` for compact signatures, accepted parameters, return shapes, and the most common gotchas.
- `references/workflows.md` for copyable recipes that combine image, video, flow, visualization, and quantization calls.
- `references/troubleshooting.md` for symptoms and recovery steps around color order, shape order, headless display, codecs, optional backends, dtype/range, and flow shape issues.
- `scripts/media_smoke_check.py` to verify the installed `mmcv` media surface with deterministic tiny arrays and temporary files.

## Scope Boundaries

- Use this sub-skill for functional APIs in `mmcv.image`, `mmcv.video`, `mmcv.visualization`, and `mmcv.arraymisc`.
- Route transform pipeline classes such as `Resize`, `Compose`, and `LoadImageFromFile` to `../data-transforms/`.
- Route CNN/layer builders to `../cnn-model-building/`.
- Route compiled `mmcv.ops` availability, build failures, and `_ext` import issues to `../ops-and-builds/`; this media surface works in `mmcv-lite` when its Python dependencies are present.

## Safety Defaults

- Prefer `show=False` plus `out_file=...` or returned arrays for visualization in headless sessions; avoid `imshow()` and `flowshow()` unless a GUI display is definitely available.
- Treat image arrays as `H, W, C`, but many MMCV size parameters are `(width, height)` and padding target `shape` is `(height, width)`.
- Treat color tuples and default image reads as BGR unless you explicitly request `channel_order='rgb'` or call a conversion helper.
- Use `backend_args` rather than deprecated `file_client_args` when reading from non-local file backends.

## Quick Validation

Run the bundled check in any environment where MMCV is installed:

```bash
python scripts/media_smoke_check.py --help
python scripts/media_smoke_check.py
```

The script checks imports, image bytes round-trip, BGR/RGB conversion, resizing scale reports, normalization/denormalization, array quantization, and optional flow helpers without reading the original repository checkout.
