---
name: visualization-interop
description: "Plot, render, convert channels/RGB, matrix/image data, and
  interoperate with NumPy, nibabel, and SimpleITK in ANTsPy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization and Interop

Use this sub-skill when a task asks for ANTsPy plotting, saved figures, headless rendering, image grids, orthographic views, movies, channel/RGB/vector handling, image-to-matrix conversion, n-dimensional image splitting/merging, or conversion to/from nibabel and SimpleITK objects.

## Start Here

1. Import the public package as `import ants`; the installable distribution is `antspyx`.
2. For CI, servers, notebooks without display access, or scripts that save figures, set a non-interactive Matplotlib backend before importing `ants`; see [workflows](references/workflows.md#headless-plot-saving).
3. Use [API reference](references/api-reference.md) for verified plotting signatures, conversion signatures, optional dependency notes, and known unsupported aliases.
4. Pick a recipe from [workflows](references/workflows.md): saved plots, overlays, grids, histograms, movies, channels/RGB/vector images, matrix/image round trips, n-dimensional image lists, nibabel, or SimpleITK.
5. Check [troubleshooting](references/troubleshooting.md) for backend failures, optional import failures, overlay mismatch, channel axis confusion, and mask/matrix ordering issues.
6. For a deterministic runtime check, run [scripts/antspy_plotting_smoke.py](scripts/antspy_plotting_smoke.py) in an environment with `antspyx`, `numpy`, and `matplotlib` installed.

## Core Rules

- Pass `filename=` to `ants.plot`, `ants.plot_ortho`, `ants.plot_ortho_stack`, and `ants.plot_grid` for non-interactive rendering; otherwise these functions call Matplotlib display behavior.
- Validate physical space before display or conversion with `ants.image_physical_space_consistency(a, b)`. Some plotting helpers resample mismatched overlays automatically, but explicit validation prevents silent interpolation mistakes.
- Plotting helpers expect scalar images for base display and overlays. Split component images, choose a scalar component, or make an RGB/vector image intentionally before plotting.
- `ants.scalar_to_rgb` is present in the namespace but is not a working scalar colorizer in current ANTsPy; use Matplotlib colormaps on arrays or explicit RGB image construction when scalar-to-RGB display is needed.
- ANTsPy component arrays use a trailing component axis. Move channel-first arrays to channel-last before `ants.from_numpy(..., has_components=True)` or `ants.from_numpy(..., is_rgb=True)`.
- Matrix rows follow the order of the input image list; matrix columns follow the voxel order selected by `mask >= epsilon`. Reuse the exact same mask and `epsilon` when converting back.

## Route Elsewhere

- Image creation, IO, metadata setters, pixel types, NumPy views/copies, and physical-space primitives: [image-core](../image-core/SKILL.md).
- Filtering, masks, thresholding, resampling, cropping, padding, denoising, morphology, histogram matching, and display preprocessing: [image-ops-math](../image-ops-math/SKILL.md).
- Registration, transform application, warped grids, transform ordering, interpolation for registration outputs, and deformation-field interpretation: [registration-transforms](../registration-transforms/SKILL.md).
- Segmentation overlays when label semantics, label ordering, or label-specific metrics matter: [segmentation-labels](../segmentation-labels/SKILL.md).
- Deep-learning patch tensors, augmentation, one-hot arrays, and learning-specific channel conventions: [learning-deeplearn](../learning-deeplearn/SKILL.md).

## References

- [API reference](references/api-reference.md): plotting, channel/RGB, matrix/image, n-dimensional list, nibabel, and SimpleITK signatures plus behavior notes.
- [Workflows](references/workflows.md): self-contained recipes for headless figures, overlays, grids, histograms, movies, channels/RGB, matrix round trips, and optional interop.
- [Troubleshooting](references/troubleshooting.md): display backend errors, optional dependency failures, physical-space mismatches, vector/RGB pitfalls, and mask ordering problems.
