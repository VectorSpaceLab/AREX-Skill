---
name: image-processing
description: "Use when working with Kornia image tensors, color conversion,
  filters, enhancement, morphology, drawing, or image I/O workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kornia image processing

Use this sub-skill for Kornia's deterministic image-processing operators: color spaces, filtering, enhancement, morphology, image drawing, tensor/image conversion, and file I/O.

## Read first

- Read `references/dtype-and-layout.md` when the task involves CHW/BCHW/HWC confusion, uint8 versus float tensors, device placement, or value ranges.
- Read `references/api-reference.md` for the main public functions and module classes to use.
- Read `references/workflows.md` for recipes that combine I/O, conversion, filtering, enhancement, and morphology.
- Read `references/troubleshooting.md` when imports, image decoding, shape checks, dtype checks, or low-precision kernels fail.
- Run `scripts/processing_smoke.py` when you need a fast public-API check before using this guidance in an environment.

## Scope

This route owns:

- `kornia.io`: `load_image`, `write_image`, `ImageLoadType`.
- `kornia.image`: `image_to_tensor`, `tensor_to_image`, drawing helpers, grid utilities, textual image rendering.
- `kornia.color`: RGB/BGR/gray, HSV/HLS, Lab/Luv/XYZ/YUV/YCbCr/raw conversions and colormaps.
- `kornia.filters`: Gaussian/box/median/bilateral/guided/motion blur, Sobel/Laplacian/Canny, filter kernels, `filter2d`/`filter3d`.
- `kornia.enhance`: brightness/contrast/gamma/hue/saturation, histogram/equalization/CLAHE, normalization, ZCA, differentiable JPEG.
- `kornia.morphology`: dilation, erosion, opening, closing, gradient, top-hat, bottom-hat.

Route elsewhere:

- Random augmentation pipelines, synchronized masks/boxes/keypoints, or `AugmentationSequential`: `../augmentation-pipelines/SKILL.md`.
- Spatial warps, homographies, camera geometry, depth, epipolar, or pose: `../geometry-vision/SKILL.md`.
- Loss functions and evaluation metrics: `../losses-and-metrics/SKILL.md`.
- Learned feature extractors or descriptor matching: `../features-and-matching/SKILL.md`.
- Model builders, ONNX, or transpilation: `../models-and-deployment/SKILL.md`.

## Operating workflow

1. Normalize the input contract before selecting an operator.
   - Image tensors are usually `(..., C, H, W)` for batched workflows or `(C, H, W)` for single images.
   - `load_image(..., ImageLoadType.RGB32)` returns a float32 RGB tensor in `[0, 1]` with shape `(3, H, W)`.
   - `write_image` accepts `(3,H,W)`, `(1,H,W)`, or `(H,W)` tensors and supports `.jpg`, `.jpeg`, `.png`, and `.tiff`.
2. Pick functionals for one-off operations and `nn.Module` wrappers when the operation belongs inside a model or pipeline.
3. Preserve device and dtype intentionally. Kornia operators generally follow the input tensor device; some linalg, FFT, or low-precision paths may promote internally or reject a dtype.
4. Validate outputs with simple assertions: expected shape, finite values, channel count, and range when applicable.
5. If combining with random augmentation, hand off after deterministic preprocessing rather than duplicating augmentation container rules here.

## Common workflows

- Decode an image with `load_image`, normalize or color-convert it, and then feed the result into a later augmentation or geometry route.
- Use `kornia.filters` or `kornia.enhance` when the task is deterministic preprocessing rather than random augmentation.
- Use morphology on masks after you have fixed layout and dtype, not before.
- Prefer `tensor_to_image` only for human-readable output or file saving; keep the working representation as tensors.

## Pitfalls

- A float tensor in `[0, 255]` looks valid but will behave as an overbright `[0, 1]` tensor in many Kornia image APIs.
- `write_image` has dtype and suffix limits; convert explicitly when saving PNG/JPEG and prefer TIFF for float32 output.
- If a function suddenly wants an image-like module from a lazy optional import, install the optional dependency or choose a no-download smoke.

## Quick validation habits

- A single-channel output is still an image tensor; keep the layout contract visible when chaining it downstream.
- If a filter or enhancement step fails on half precision, rerun in float32 before changing the algorithm.
- Use `write_image` only after choosing the correct extension and dtype for the chosen file format.
- When the input came from a non-Kornia library, convert once at the boundary and keep Kornia tensors thereafter.

## Quick smoke

```bash
python scripts/processing_smoke.py --device auto
python scripts/processing_smoke.py --device cpu --with-io-roundtrip
```

Expected terminal signal: `processing-smoke-ok`.

## Native evidence candidates

For future verification, representative native candidates include color, filters, enhance, morphology, image, and I/O tests. Use targeted CPU float32 cases first; CUDA, MPS, and low-precision matrices are optional backend coverage rather than the minimum operating contract.
