---
name: image-core
description: "Create, read, write, inspect, clone, index, compare, and validate
  ANTsPy ANTsImage objects while preserving physical-space metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ANTsPy Image Core

Use this sub-skill when a task is about the `ants.ANTsImage` lifecycle: constructing images from NumPy arrays, reading or writing image files, inspecting pixel type and physical metadata, cloning or casting images, indexing image data, comparing image values, checking physical-space consistency, or using packaged ANTsPy fixture data.

## Start Here

1. Import the public package as `import ants`; the package distribution is `antspyx`.
2. For verified signatures, parameter notes, metadata semantics, and dtype rules, read [API reference](references/api-reference.md).
3. For practical recipes, use [workflows](references/workflows.md) for creation, IO, NumPy round trips, metadata repair, indexing, and vector/RGB images.
4. For common failures, use [troubleshooting](references/troubleshooting.md) before changing image data or metadata.
5. For a tiny deterministic runtime check, run [scripts/antspy_image_smoke.py](scripts/antspy_image_smoke.py) in an environment with `antspyx` installed.

## Core Rules

- `ANTsImage` stores voxel values plus physical-space metadata: `origin`, `spacing`, `direction`, `dimension`, `pixeltype`, `dtype`, `shape`, `components`, and RGB/vector flags.
- `img.numpy()` returns a copy; editing it does not mutate the image. `img.view()` returns shared memory; editing it mutates the image.
- `ants.from_numpy(array)` uses default physical metadata unless `origin`, `spacing`, and `direction` are passed. Prefer `img.new_image_like(array)` or `ants.from_numpy_like(array, img)` for metadata-preserving array transforms.
- Image-image arithmetic and image-mask indexing require matching physical space. Check with `ants.image_physical_space_consistency(a, b)`; use `datatype=True` when pixel type and component count must also match.
- `ants.allclose(a, b)` compares voxel arrays only and does not prove matching physical metadata.
- Supported scalar pixel types are `unsigned char`, `unsigned int`, `float`, and `double`; NumPy names map to `uint8`, `uint32`, `float32`, and `float64` with constructor caveats in [API reference](references/api-reference.md#pixeltype-and-dtype-rules).

## Route Elsewhere

- Filtering, masks, thresholding, `iMath`, morphology, cropping/padding, denoising, and resampling details: [image-ops-math](../image-ops-math/SKILL.md).
- Registration workflows, transform application chains, transform IO, displacement fields, motion correction, Jacobians, and templates: [registration-transforms](../registration-transforms/SKILL.md).
- Segmentation, labels, overlap metrics, label geometry, label matrices, and point images: [segmentation-labels](../segmentation-labels/SKILL.md).
- Plotting, RGB display, animation, image-to-matrix interop, nibabel, SimpleITK, and external visualization formats: [visualization-interop](../visualization-interop/SKILL.md).
- Deep learning patch extraction, augmentation, one-hot utilities, and learning-specific array/image preparation: [learning-deeplearn](../learning-deeplearn/SKILL.md).

## Boundary Notes

- `ants.ANTsTransform`, `ants.create_ants_transform`, `ants.read_transform`, and `ants.write_transform` are mentioned here only to distinguish image metadata from transform objects. Use [registration-transforms](../registration-transforms/SKILL.md) for transform construction, application, composition, inversion, or registration output handling.
- Channel utilities such as `merge_channels`, `split_channels`, `rgb_to_vector`, and `vector_to_rgb` are core enough for diagnosing vector/RGB `ANTsImage` shape and component semantics; display-oriented RGB workflows route to visualization/interop.

## References

- [API reference](references/api-reference.md): verified signatures, properties, constructors, IO, metadata setters/getters, pixel types, indexing, comparisons, fixture data, and transform-routing boundaries.
- [Workflows](references/workflows.md): self-contained recipes for image creation, read/write, NumPy conversion, metadata validation, indexing, component images, and fixture use.
- [Troubleshooting](references/troubleshooting.md): import/backend failures, dtype and list input errors, physical-space mismatches, RGB/vector component confusion, IO/header failures, and indexing pitfalls.
