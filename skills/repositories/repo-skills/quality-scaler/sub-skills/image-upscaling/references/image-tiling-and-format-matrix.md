# Image tiling and format matrix

## Purpose

Read this when the image job depends on supported formats, model scale factors, or the tile threshold.

## Model and scale matrix

| Model family | Scale | Notes |
| --- | --- | --- |
| `LVAx2` | x2 | low-scale image model |
| `RealESR_Gx4`, `RealESR_Ax4`, `BSRGANx4`, `RealESRGANx4`, `MSharpx4` | x4 | main enlargement paths |
| `BSRGANx2` | x2 | smaller-scale BSRGAN path |
| `IRCNN_Mx1`, `IRCNN_Lx1` | x1 | restore-style paths |

## Supported image formats

- JPEG variants: `.jpg`, `.jpeg`, and case variants.
- PNG variants: `.png` and case variants.
- Bitmap variants: `.bmp` and case variants.
- TIFF variants: `.tif`, `.tiff`, and case variants.
- WebP variants: `.webp` and case variants.
- HEIC variants: `.heic`.

## Tiling rule

- The image is tiled when `width * height > tiles_resolution * tiles_resolution`.
- The tile count is computed from the image size and the tile budget.
- The image is split into equal-size tiles using integer division.
- The final image is stitched back together after each tile is upscaled.

## VRAM-related selection behavior

The GUI uses a model-specific factor to adjust the tile budget. The selected VRAM value is multiplied by a per-model factor before the final tile threshold is computed.

## Blending options

- `OFF` -> no blend
- `Low` -> `0.3`
- `Medium` -> `0.5`
- `High` -> `0.7`

## Caveat to remember

Because the split step uses integer division, large images whose dimensions are not neatly divisible by the tile count can lose a narrow border if you rely on a tiled path. When precision matters, test on a tiny fixture and verify the output dimensions and edges.
