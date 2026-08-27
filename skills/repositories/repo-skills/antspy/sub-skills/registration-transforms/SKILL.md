---
name: registration-transforms
description: "Register ANTsPy images and manage transform application, transform
  IO, displacement fields, motion correction, templates, landmarks, and Jacobian
  diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ANTsPy Registration and Transforms

Use this sub-skill when a task is about image registration, transform lists, applying transforms to images or points, transform object IO, displacement-field composition/inversion, motion correction, template building, Jacobian/deformation diagnostics, warped grids, landmarks, or FSL-to-ANTs linear transform conversion.

## Start Here

1. Import the public package as `import ants`; the package distribution is `antspyx`.
2. Choose the cheapest transform family that can solve the task using [transform types](references/transform-types.md).
3. Check verified signatures, return keys, transform-list rules, and IO helpers in [API reference](references/api-reference.md).
4. Use [workflows](references/workflows.md) for fast rigid/affine registration, transform application to images/points, multi-metric registration, motion correction, template building, Jacobians, displacement fields, landmarks, and validation.
5. Use [troubleshooting](references/troubleshooting.md) when output is misplaced, labels are interpolated incorrectly, transform files are missing, dimensions disagree, or SyN is too slow.
6. Run [scripts/antspy_registration_smoke.py](scripts/antspy_registration_smoke.py) for a tiny bounded runtime check in an environment with `antspyx` installed.

## Core Contracts

- `ants.registration(fixed, moving, ...)` returns `warpedmovout`, `warpedfixout`, `fwdtransforms`, and `invtransforms`; time-varying registrations can also return `velocityfield`.
- Use `tx["fwdtransforms"]` with `ants.apply_transforms(fixed=fixed, moving=moving, ...)` to resample the moving image into the fixed image domain.
- Point mapping follows the opposite practical convention from image resampling: use physical-coordinate point DataFrames and set `whichtoinvert` deliberately, especially for affine `.mat` files.
- `whichtoinvert` must have one boolean per transform; only matrix transforms can be inverted this way, never warp/displacement-field files.
- Prefer `Translation`, `Rigid`, `QuickRigid`, `AffineFast`, or `antsRegistrationSyNQuick[...]` with explicit iteration limits for tests and debugging; default nonlinear SyN can be expensive.
- Transform files are produced as task-owned runtime outputs. If they must be reused, set an explicit writable `outprefix` or composition filename and keep those files with the task output.

## Route Elsewhere

- Create, read, write, inspect, clone, compare, and repair `ANTsImage` physical metadata: [image-core](../image-core/SKILL.md).
- Preprocess before registration with masks, smoothing, denoising, cropping, thresholding, histogram matching, morphology, or resampling: [image-ops-math](../image-ops-math/SKILL.md).
- Use transformed outputs for segmentation, label overlap, label geometry, or label statistics: [segmentation-labels](../segmentation-labels/SKILL.md).
- Plot warped images, grids, overlays, animations, or external visualization formats: [visualization-interop](../visualization-interop/SKILL.md).
- Use transforms inside learning-specific augmentation or patch pipelines: [learning-deeplearn](../learning-deeplearn/SKILL.md).

## Boundary Notes

- This sub-skill covers registration mechanics and transform semantics. It does not teach image loading, mask construction, segmentation interpretation, or plotting beyond routing to the relevant sub-skill.
- `ants.apply_transforms` can resample label images, but choose label-safe interpolation here and handle label-specific analysis in `segmentation-labels`.
- Landmark helpers use physical coordinates. Convert voxel indices with image-core coordinate utilities before applying point transforms.

## References

- [API reference](references/api-reference.md): verified public signatures, registration dict keys, transform application, transform IO, displacement helpers, landmarks, and FSL conversion.
- [Workflows](references/workflows.md): bounded registration recipes, image/point transform application, multi-metric registration, motion correction, templates, Jacobians, fields, landmarks, and validation checks.
- [Transform types](references/transform-types.md): transform family selection, speed/quality tradeoffs, inversion/order semantics, interpolators, `imagetype`, and composite/displacement outputs.
- [Troubleshooting](references/troubleshooting.md): wrong transform direction, dimension/metadata mismatch, interpolation problems, missing files, expensive registrations, and temporary-output expectations.
