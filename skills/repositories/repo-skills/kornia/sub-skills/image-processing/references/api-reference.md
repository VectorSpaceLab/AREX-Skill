# Image-processing API reference

This is a compact routing reference for common Kornia image-processing APIs. Use the package docs or live `inspect.signature` only when a task needs a rarely used argument not listed here.

## I/O and conversion

| API | Use | Notes |
| --- | --- | --- |
| `kornia.io.load_image(path_file, desired_type=ImageLoadType.RGB32, device="cpu")` | Decode image files through the Kornia Rust backend. | Returns CHW tensor; RGB32/GRAY32 scale to float `[0,1]`; RGB8/GRAY8 keep uint8. |
| `kornia.io.write_image(path_file, image, quality=80)` | Save image tensor to jpg/jpeg/png/tiff. | Accepts `(3,H,W)`, `(1,H,W)`, or `(H,W)`; PNG/JPEG are usually uint8; float32 writing is TIFF-only. |
| `kornia.image.image_to_tensor` / `tensor_to_image` | Convert between array-like images and tensors. | Use to bridge HWC libraries and CHW Kornia tensors. |
| `kornia.image.draw_line`, `draw_rectangle`, `draw_point2d`, `draw_convex_polygon` | Draw geometric annotations on tensors. | Validate coordinate order and channel count before drawing. |

## Color

| API family | Typical functions/classes | Notes |
| --- | --- | --- |
| RGB/BGR/gray | `rgb_to_grayscale`, `grayscale_to_rgb`, `rgb_to_bgr`, `bgr_to_rgb` | Keep channel placement as CHW/BCHW. |
| Alpha | `rgb_to_rgba`, `rgba_to_rgb`, `bgr_to_rgba`, `rgba_to_bgr` | Dropping alpha is a semantic choice; do it explicitly. |
| Perceptual/physical spaces | `rgb_to_hsv`, `rgb_to_hls`, `rgb_to_lab`, `rgb_to_luv`, `rgb_to_xyz`, and inverses | Inputs are normally floating RGB in a valid range. |
| Video/raw formats | `rgb_to_yuv`, `rgb_to_yuv420`, `rgb_to_yuv422`, `rgb_to_raw`, and inverses | Check channel and subsampling expectations before batching. |
| Colormap | `apply_colormap`, `ColorMap`, `ApplyColorMap` | Useful for visualizing single-channel response maps. |

## Filters

Representative signatures:

```python
kornia.filters.gaussian_blur2d(input, kernel_size, sigma, border_type="reflect", separable=True)
kornia.filters.median_blur(input, kernel_size)
kornia.filters.box_blur(input, kernel_size, border_type="reflect", normalized=True)
kornia.filters.canny(input, low_threshold=0.1, high_threshold=0.2, ...)
kornia.filters.sobel(input, normalized=True, eps=1e-6)
```

Use functional calls for simple processing and module wrappers such as `GaussianBlur2d`, `MedianBlur`, `Canny`, `Sobel`, `Laplacian`, `BoxBlur`, and `MotionBlur` inside `nn.Module` pipelines.

## Enhancement

Common APIs include:

- `adjust_brightness`, `adjust_contrast`, `adjust_gamma`, `adjust_hue`, `adjust_saturation`, `adjust_sigmoid`, `adjust_log`.
- `equalize`, `equalize3d`, `equalize_clahe`, `histogram`, `histogram2d`, `image_histogram2d`.
- `normalize`, `denormalize`, `normalize_min_max`, `zca_mean`, `zca_whiten`, `linear_transform`.
- `jpeg_codec_differentiable` for differentiable JPEG-like degradation.

Many of these have module forms (`AdjustBrightness`, `Normalize`, `ZCAWhitening`, `JPEGCodecDifferentiable`) when you need reusable PyTorch modules.

## Morphology

Use `dilation`, `erosion`, `opening`, `closing`, `gradient`, `top_hat`, and `bottom_hat`. Kernels are PyTorch tensors; keep them on the same device as the image or move them before the call.

```python
kernel = torch.ones(3, 3, device=image.device)
out = kornia.morphology.dilation(image, kernel)
```
