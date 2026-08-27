---
name: image-ops-math
description: "Use ANTsPy image operations for smoothing, resampling, masking,
  cropping, morphology, iMath, bias correction, histogram matching, and image
  metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Image Operations and Math

Use this sub-skill when a task asks for ANTsPy preprocessing, filtering, masks, crop/pad/slice, resampling, intensity normalization, morphology, `iMath`, similarity metrics, neighborhood extraction, or quantitative image utilities.

## Route First

- Use [image-core](../image-core/) for image creation, IO, cloning, pixel types, metadata checks, NumPy conversion, and physical-space consistency helpers before applying operations here.
- Use [registration-transforms](../registration-transforms/) for registration, non-identity transform application, transform ordering, point transforms, and transform output troubleshooting.
- Use [segmentation-labels](../segmentation-labels/) for label statistics, label geometry, label overlap, segmentation workflows, and multi-label morphology beyond generic binary/grayscale operations.
- Use [visualization-interop](../visualization-interop/) for plotting, screenshots, notebook display, and conversions whose purpose is visualization.

## Read These References

- [API reference](references/api-reference.md): verified public signatures, parameter choices, chainable methods, and scalar/vector/RGB caveats.
- [Workflows](references/workflows.md): preprocessing, masks, resampling, bias correction, morphology, metrics, neighborhood, and validation recipes.
- [iMath reference](references/imath-reference.md): ANTsPy-recognized `iMath` operations, helper wrappers, operation families, and unsupported-operation recovery.
- [Troubleshooting](references/troubleshooting.md): interpolator mistakes, physical-vs-voxel resampling, mask dimensionality, iMath failures, backend errors, and expensive 3D operations.
- [Smoke script](scripts/antspy_ops_smoke.py): tiny in-memory check covering threshold, smoothing, resampling, masking, iMath, morphology, metrics, and expected error recovery.

## Default Patterns

- Prefer `ants.resample_image_to_target(image, target, interp_type="linear")` when output must inherit another image's shape, spacing, origin, and direction; use `"nearestNeighbor"` or `"genericLabel"` for label images.
- Use `ants.resample_image(image, params, use_voxels=True, interp_type=0)` when `params` are output voxel counts; use `use_voxels=False` when `params` are new physical spacing values.
- Build tiny or synthetic masks with `ants.get_mask(image, low_thresh=..., high_thresh=..., cleanup=0)` because default cleanup can erase small objects.
- Use `ants.iMath(image, "Normalize")`, `ants.iMath(image, "TruncateIntensity", low, high, bins)`, or helper wrappers such as `ants.iMath_normalize(image)` for common operations.
- Split long chained `ANTsImage` calls when a step changes shape or physical space so you can inspect `dimension`, `shape`, `spacing`, `origin`, and `direction` before combining images.
