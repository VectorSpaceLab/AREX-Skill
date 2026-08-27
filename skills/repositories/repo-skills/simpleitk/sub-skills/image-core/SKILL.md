---
name: image-core
description: "Work with SimpleITK Image objects, spatial metadata,
  pixel/component types, physical coordinates, and NumPy array conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleITK Image Core

Use this sub-skill when a task involves constructing or inspecting `sitk.Image` objects, preserving `origin`/`spacing`/`direction`, converting between index and physical coordinates, reading or writing individual pixels, diagnosing pixel/component ids, or bridging images to NumPy arrays.

## Start Here

- Read [references/image-model.md](references/image-model.md) for the SimpleITK physical image model, spatial metadata, coordinate conversions, pixel/component categories, metadata dictionary basics, and validation checks.
- Read [references/numpy-bridge.md](references/numpy-bridge.md) for `sitk.GetArrayFromImage`, `sitk.GetArrayViewFromImage`, `sitk.GetImageFromArray`, reversed shape order, vector image component axes, dtype mapping, and metadata preservation after array processing.
- Read [references/api-reference.md](references/api-reference.md) for concise verified constructor patterns, image methods, pixel inspection APIs, NumPy bridge behavior, and copy/view notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when debugging metadata loss, reversed NumPy shapes, read-only array views, unsupported dtypes, wrong `isVector` choices, component mismatches, direction errors, or out-of-bounds indices.
- Run [scripts/inspect_image_metadata.py](scripts/inspect_image_metadata.py) to print JSON metadata for a readable image file or a deterministic built-in demo image from any current working directory.

## Quick Routing

- For `ReadImage`, `WriteImage`, registered ImageIOs, DICOM tags, series discovery, file formats, or dataset examples, route to [../io-and-data/SKILL.md](../io-and-data/SKILL.md).
- For smoothing, thresholding, morphology, connected components, segmentation, measurements, or label workflows beyond basic pixel/type inspection, route to [../filtering-segmentation/SKILL.md](../filtering-segmentation/SKILL.md).
- For registration, resampling, transforms as processing objects, interpolators, displacement fields, or coordinate-frame alignment workflows, route to [../registration-transforms/SKILL.md](../registration-transforms/SKILL.md).
- For source builds, wrapping internals, optional elastix/transformix availability, packaging, or compiled feature differences, route to [../builds-and-wrapping/SKILL.md](../builds-and-wrapping/SKILL.md).

## Essential Rules

- Import the public package as `import SimpleITK as sitk`; the Python distribution name is `simpleitk`.
- Treat an `Image` as a pixel buffer plus physical geometry. Preserve `GetOrigin()`, `GetSpacing()`, and `GetDirection()` whenever replacing pixels or rebuilding from NumPy.
- Use SimpleITK index order `(x, y, z, ...)`; NumPy scalar arrays expose spatial axes in reverse order such as `(z, y, x)` for 3D.
- `sitk.GetArrayFromImage(image)` returns a mutable deep copy; `sitk.GetArrayViewFromImage(image)` returns a read-only view tied to the image buffer.
- `sitk.GetImageFromArray(array, isVector=None)` creates a new image with default geometry, reverses spatial axes, and treats the final axis as components only when vector conversion applies.
