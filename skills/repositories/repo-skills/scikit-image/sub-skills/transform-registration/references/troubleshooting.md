# Transform and Registration Troubleshooting

## Warp moves the image the wrong way

`warp` expects an inverse map: output coordinates are mapped back into the source image. If you have a forward transform, pass `tform.inverse`.

Common fixes:

- Use `warp(image, tform.inverse)` when `tform` maps source points to destination points.
- Remember that `rotate` takes degrees, but transform classes such as `AffineTransform` and `SimilarityTransform` take rotation in radians.
- `rotate(center=...)` uses `(cols, rows)`, not `(rows, cols)`.
- `warp_polar(center=...)` uses `(row, col)`.
- `phase_cross_correlation` returns the correction shift in `(row, col, ...)` order.

If you only need to transform points, use `matrix_transform` instead of `warp`.

## Channel axis or dtype looks wrong

Several geometry helpers convert inputs to floating point. That is normal.

- `resize` expects channels last and does not take `channel_axis`.
- `rescale`, `resize_local_mean`, `warp_polar`, and `pyramid_*` accept `channel_axis` when the channel axis is not last.
- `warp` and `rotate` work naturally with channels last.
- `preserve_range=True` keeps the native intensity scale, but does not guarantee the original dtype.
- `resize_local_mean`, `downscale_local_mean`, and interpolated warps can still return floating output.

For discrete masks or edge maps, use `order=0` and keep `anti_aliasing=False`.

## Downsampling looks blurry or aliased

`resize` and `rescale` usually need anti-aliasing when you downsample.

- Leave `anti_aliasing=True` for ordinary grayscale or intensity images.
- Use `downscale_local_mean` when the scale factor is an integer and you want exact block means.
- Use `resize_local_mean` when you want area-based resizing to a target shape.
- Do not enable anti-aliasing on boolean arrays.

If the result should preserve hard edges, nearest-neighbor interpolation (`order=0`) is usually the right choice.

## Transform estimation failed

`estimate_transform` and `from_estimate` can fail when the point set is degenerate or inconsistent.

Check for:

- repeated points,
- collinear points when the model needs area,
- too few correspondences,
- source and destination arrays with mismatched shapes.

Recommended response:

```python
if not tform:
    raise RuntimeError(f'Failed estimation: {tform}')
```

If the correspondences are noisy, let the `analysis` route produce the inlier point pairs first.

## Phase cross-correlation is confusing

`phase_cross_correlation` returns the correction needed to align the moving image to the reference image.

- If you synthesized the moving image with `fourier_shift(..., shift)` or `ndi.shift(..., shift)`, expect the returned correction to be the negative of that shift.
- `space='fourier'` only makes sense when both inputs are already Fourier transformed.
- `disambiguate=True` helps when the true translation is larger than half the image size.
- If `reference_mask` or `moving_mask` is provided, `upsample_factor` and `space` are ignored.
- NaNs or empty valid regions usually lead to warnings and unusable error values.

When the correction looks off by one axis, recheck row/column order before warping.

## Angle units do not match

This route uses several angle conventions:

- `rotate` uses degrees.
- `SimilarityTransform`, `AffineTransform`, and related classes use radians for their rotation parameters.
- `radon` and `iradon` use degrees for `theta`.
- `hough_line` and `probabilistic_hough_line` use radians for `theta`.

If a result looks rotated by the right amount but the wrong sign, the issue is usually a unit or axis-order mismatch rather than the estimator itself.

## Hough peaks are missing or noisy

Hough helpers expect edge-like binary input.

- Make sure the input already contains edges or line/circle/ellipse pixels.
- Tune `threshold`, `min_distance`, `min_angle`, `min_xdistance`, `min_ydistance`, `line_length`, `line_gap`, `normalize`, and `total_num_peaks`.
- Use `rng=` with `probabilistic_hough_line` if you need reproducible results.
- `hough_line_peaks` returns `accum, angles, dists`.
- `hough_circle_peaks` returns `accum, cx, cy, rad`.
- `hough_ellipse` returns a structured array; sort by `accumulator` before reading the best row.

## Optical flow looks flipped or unstable

The optical-flow solvers only accept grayscale inputs.

- Convert RGB data first, usually with `rgb2gray`.
- Use floating-point inputs and `dtype=np.float32` or `dtype=np.float64`.
- The returned flow has one component per axis, so the 2-D warp uses `row_coords + v` and `col_coords + u`.
- `optical_flow_ilk` is faster but can be less accurate on flat regions and sharp boundaries.
- `optical_flow_tvl1` is heavier but often gives smoother registration.

If the warped frame still looks misaligned, inspect the sign of each flow component separately.

## Pyramid output is not what you expected

Pyramid helpers return float images and stop when the image can no longer shrink.

- `max_layer=-1` means build all possible layers.
- `pyramid_gaussian` yields the original image first.
- `pyramid_laplacian` yields residual layers, not ordinary downsampled images.
- Use `channel_axis` when the multichannel axis is not last.

If a pyramid layer shape surprises you, check whether the channel axis was included in the resize factors or passed separately.
