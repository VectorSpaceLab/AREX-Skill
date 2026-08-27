---
name: enhancement
description: "Adjust color, exposure, filters, and restoration workflows in
  scikit-image, with explicit channel-axis and preserve-range handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Enhancement

Use this sub-skill when the task changes pixel appearance or intensity statistics rather than geometry or object bookkeeping.

## Route here

- Convert between color spaces, remove alpha, or overlay existing labels with `skimage.color`.
- Adjust contrast, histogram shape, and intensity ranges with `skimage.exposure`.
- Smooth, sharpen, detect edges, or choose a cutoff with `skimage.filters`.
- Denoise, inpaint, deblur, subtract background, unwrap phase, or stabilize denoising with `skimage.restoration`.

## Fast start

1. Inspect `shape`, `dtype`, `min`, `max`, and whether the array has a channel dimension.
2. Set `channel_axis` explicitly for every multichannel image; use `None` for scalar or grayscale images.
3. Use `preserve_range=True` whenever a function offers it and the numeric values should stay in their native units.
4. Convert to float or back to storage dtype only when that is the intended next step.
5. Verify the result on a small sample before chaining multiple enhancement steps.

## Working rules

- `channel_axis` is about layout, not color meaning. Do not rely on defaults for color images.
- `preserve_range` is about value semantics, not dtype. Keep it on when the values already mean something physically or when later steps must not renormalize to `[0, 1]`.
- Many enhancement functions return float arrays; convert the result afterward with `img_as_*` only when storage or downstream APIs need it.
- Thresholding belongs here only as preprocessing. If the task needs connected components, region labeling, or object statistics, route elsewhere.
- `label2rgb` is a display helper for existing labels, not a segmentation step.

## Boundaries

- Do not cover segmentation, morphology cleanup, connected components, or label creation.
- Do not cover region properties, object statistics, or image-quality metrics.
- Do not cover geometric transforms, warps, alignment, or registration.
- If a function does not expose `channel_axis`, either convert to a scalar image first or handle channels explicitly one at a time.

## References

- `references/workflows.md`
- `references/troubleshooting.md`
