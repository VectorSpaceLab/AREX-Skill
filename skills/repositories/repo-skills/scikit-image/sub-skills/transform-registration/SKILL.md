---
name: transform-registration
description: "Geometric transforms, warps, pyramids, Radon/Hough helpers, phase
  cross-correlation, and optical flow for scikit-image."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Transform and Registration

Use this sub-skill when you need to align images, warp coordinates, change scale, build pyramids, reconstruct from projections, or estimate dense motion with scikit-image. Keep point-feature extraction, descriptor matching, and segmentation in other routes.

## Route by Task

- **Warp, rotate, rescale, resize, swirl, or polar-warp an image**: use [`references/workflows.md#warp-resize-and-pyramids`](references/workflows.md#warp-resize-and-pyramids).
- **Apply a local nonlinear warp or custom coordinate field**: use [`references/workflows.md#custom-coordinate-fields-and-swirl`](references/workflows.md#custom-coordinate-fields-and-swirl).
- **Estimate a transform from point pairs**: use [`references/workflows.md#estimate-a-transform-from-point-pairs`](references/workflows.md#estimate-a-transform-from-point-pairs).
- **Run Radon or Hough geometry helpers**: use [`references/workflows.md#radon-and-hough-workflows`](references/workflows.md#radon-and-hough-workflows).
- **Register translation, rotation, or scale**: use [`references/workflows.md#phase-cross-correlation-and-log-polar-registration`](references/workflows.md#phase-cross-correlation-and-log-polar-registration).
- **Estimate dense motion fields**: use [`references/workflows.md#optical-flow-registration`](references/workflows.md#optical-flow-registration).

## Core Rules

- `warp` takes an inverse map. Pass a transform object, its `.inverse`, a 3×3 matrix, a callable inverse map, or a coordinate array. For 2-D homographies, `SimilarityTransform`, `AffineTransform`, and `ProjectiveTransform` use a faster matrix path.
- `resize`, `rescale`, `resize_local_mean`, `warp_polar`, and `pyramid_*` accept `channel_axis`; `warp` and `rotate` assume a normal image layout, so move channels before calling them if needed.
- Use `preserve_range=True` when the input intensities must stay on their native scale. Interpolated warps usually return floating output; use `order=0` for discrete masks or edge maps.
- `phase_cross_correlation` returns the correction shift in input axis order, not the original motion. If the images may differ by more than half the frame, use `disambiguate=True`.
- `optical_flow_ilk` and `optical_flow_tvl1` require grayscale images and return one flow component per axis.
- `radon` and `iradon` use projection angles in degrees. `hough_line` and `probabilistic_hough_line` use theta in radians.
- If `from_estimate` or `estimate_transform` fails, check `bool(tform)` before warping.
- Use `matrix_transform` for point arrays and `warp_coords` for reusable custom coordinate grids.

## What Stays Out

- If you need corners, descriptors, or matched keypoints first, use `analysis`.
- If you need thresholds, morphology, masks, or region cleanup first, use `segmentation-and-shapes`.
- If you only need intensity normalization or denoising, use `enhancement`.

## Reference Files

- [`references/workflows.md`](references/workflows.md) for the main geometry, registration, tomography, and motion recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for inverse-map, axis-order, dtype, mask, and angle-unit fixes.
