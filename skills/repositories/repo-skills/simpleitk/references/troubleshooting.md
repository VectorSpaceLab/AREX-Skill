# Cross-Cutting Troubleshooting

Use this page when a SimpleITK task fails before it clearly belongs to one sub-skill, or when the symptom spans install, import, image geometry, IO, filters, registration, and optional compiled features.

## `import SimpleITK` Fails

Symptoms:

- `ModuleNotFoundError: No module named 'SimpleITK'`.
- Shared-library load errors after installation.
- A package appears installed but the running interpreter cannot import it.

Actions:

1. Verify the same interpreter owns the install: `python -m pip show simpleitk` and `python - <<'PY'` with `import SimpleITK as sitk`.
2. Prefer `python -m pip install simpleitk` for ordinary Python use, or a conda-forge-only environment for conda projects.
3. Run `scripts/check_simpleitk_env.py` after import succeeds to inspect version, ImageIO, NumPy, registration, and optional wrappers.
4. Route source-build failures to `sub-skills/builds-and-wrapping/SKILL.md` instead of debugging them as image-processing API issues.

## Installed Version Differs From Checkout Docs

Symptoms:

- A checkout branch documents a feature that a local wheel does not expose.
- Optional classes are present in source but absent in the installed package.
- A development branch version differs from PyPI or conda-forge version.

Actions:

- Confirm runtime availability with `hasattr(sitk, "FeatureName")` or the nearest bundled diagnostic script.
- Use public binary-package behavior for normal user workflows.
- If the task needs a current-checkout feature, route to `sub-skills/builds-and-wrapping/SKILL.md` and plan a source build only after confirming the cost.

## ImageIO or DICOM Problems

Symptoms:

- `ReadImage` cannot determine an ImageIO backend.
- A DICOM directory returns no series IDs.
- Pixel values change after read/write.

Actions:

1. Use `sitk.ImageFileReader().GetRegisteredImageIOs()` and `sitk.ImageFileWriter().GetRegisteredImageIOs()` for backend discovery.
2. Use `sub-skills/io-and-data/SKILL.md` for suffix choices, explicit `imageIO`, DICOM series discovery, metadata tags, and transform IO.
3. Prefer `.mha` or `.nrrd` for deterministic round trips; avoid JPEG for equality checks.
4. Use explicit `outputPixelType` only when the cast is intentional, such as reading registration inputs as `sitk.sitkFloat32`.

## Lost Geometry or Wrong NumPy Shape

Symptoms:

- Output image loses spacing, origin, or direction after NumPy processing.
- NumPy shape appears reversed relative to SimpleITK size.
- A vector image has the wrong component axis.

Actions:

1. Route to `sub-skills/image-core/SKILL.md`.
2. Remember SimpleITK size/index order is `(x, y, z, ...)`; NumPy arrays are reversed spatially, such as `(z, y, x)`.
3. After `sitk.GetImageFromArray`, copy geometry from the source image when the derived image occupies the same physical space.
4. Use `isVector=True` only when the last NumPy axis represents pixel components.

## Filter or Segmentation Output Looks Wrong

Symptoms:

- Filter rejects an image due to pixel type or dimension.
- Segmentation is empty or unexpectedly huge.
- N4 or fast marching is slow or unstable.

Actions:

1. Route to `sub-skills/filtering-segmentation/SKILL.md`.
2. Check image pixel type and dimension before running the filter.
3. Validate seeds, masks, thresholds, and physical spacing.
4. Use the bundled filtering smoke script for a known-good tiny synthetic workflow before debugging user data.

## Registration or Resampling Fails

Symptoms:

- Registration fails with no valid points, no overlap, or too few samples.
- `Resample` output is all black.
- Transform direction appears inverted.
- Repeated registration results differ.

Actions:

1. Route to `sub-skills/registration-transforms/SKILL.md`.
2. Verify fixed/moving physical domains overlap after initialization.
3. Use `GetInverse()` when the transform direction is opposite the resampling need.
4. Fix metric sampling seeds and reduce global threads only when reproducibility matters more than speed.
5. Use nearest-neighbor interpolation for label images and linear interpolation for intensity images.

## Missing Elastix or Transformix Classes

Symptoms:

```python
hasattr(sitk, "ElastixImageFilter")
hasattr(sitk, "TransformixImageFilter")
```

returns `False`.

Actions:

- Treat these classes as optional and build-dependent.
- For ordinary registration, use `ImageRegistrationMethod` via `sub-skills/registration-transforms/SKILL.md`.
- If elastix/transformix is required, route to `sub-skills/builds-and-wrapping/SKILL.md` to plan a source build with elastix support, then confirm class presence after install.

## Build Starts Unexpectedly

Symptoms:

- `pip install simpleitk` starts CMake or native compilation.
- CMake asks for `ITK_DIR`.
- SWIG, compiler, or Python development headers are missing.

Actions:

1. Stop and decide whether a binary package is sufficient.
2. Upgrade `pip` and try `python -m pip install --only-binary=:all: simpleitk` to force a clear binary-selection result.
3. Use conda-forge if appropriate.
4. If source build is truly needed, route to `sub-skills/builds-and-wrapping/SKILL.md`; source builds can be expensive and may download/build dependencies.
