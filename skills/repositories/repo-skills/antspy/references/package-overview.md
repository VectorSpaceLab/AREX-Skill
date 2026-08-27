# ANTsPy Package Overview

ANTsPy is the Python interface to Advanced Normalization Tools for biomedical image analysis. The installable distribution is `antspyx`; the public import module is `ants`.

## What This Skill Covers

- Medical image IO and `ANTsImage` object handling.
- Physical-space metadata: `origin`, `spacing`, `direction`, `dimension`, `shape`, pixel type, scalar/vector/RGB components, and consistency checks.
- Image operations and math: smoothing, thresholding, masking, crop/pad/slice, resampling, denoising, bias correction, morphology, `iMath`, similarity, neighborhoods, and metrics.
- Registration and transforms: transform selection, registration outputs, image and point transform application, transform IO, displacement fields, motion correction, templates, warped grids, and Jacobians.
- Segmentation and labels: Atropos, k-means, Otsu, priors, joint label fusion, label statistics, overlap, geometry, matrices, centroids, and point images.
- Visualization and interop: plotting, headless rendering, overlays, channels/RGB/vector images, matrix/image conversions, nibabel, and SimpleITK.
- Learning helpers: sparse/eigen utilities, patches, augmentation, one-hot labels, simulated bias fields, regression matching, and learning-oriented crop/pad utilities.

## What This Skill Does Not Cover

- Full ANTsPyNet model training or pretrained neural-network inference.
- General ANTs C++ command-line usage outside Python `ants` APIs.
- Long-running benchmark-scale registration, template building, joint label fusion, or training-like experiments unless the user explicitly accepts runtime cost.
- Repository release engineering beyond concise install/build troubleshooting.

## Installation and Import

Use a public install path:

```bash
pip install antspyx
python -c "import ants; print(ants.__name__)"
```

or:

```bash
conda install conda-forge::antspyx
python -c "import ants; print(ants.__name__)"
```

ANTsPy includes compiled native code. If import fails after installation, check for wheel/platform compatibility, source-tree shadowing, missing compiled libraries, or an unsupported Python/platform combination before changing workflow code.

## Version Notes

The source checkout used to create this skill declares package version `0.6.4`. Live API inspection used a verified `antspyx` wheel at version `0.6.3` because rebuilding the current checkout would require a broad local ANTs/ITK/CMake native build. Source files and documentation were used for current-version deltas; live signatures and smoke scripts were verified against the installed wheel.

## Data Model Shortcuts

- `ANTsImage` wraps an image pointer plus voxel metadata and array accessors.
- `img.numpy()` returns a NumPy copy; `img.view()` exposes shared memory.
- Image arithmetic and mask/index interactions should be physically consistent, not only shape-compatible.
- Registration transform lists are ordered outputs from ANTs and must be applied with explicit image or point semantics.
- Segmentation label images should be integer-like and physically aligned with intensity images before statistics or overlap.
