# Registration and Transform Troubleshooting

## Warped Image Lands in the Wrong Place

Symptoms: the warped moving image is farther from the fixed image, overlays look reversed, or applying `invtransforms` appears to repeat the deformation.

Checks and fixes:

- For moving-to-fixed image resampling, use `tx["fwdtransforms"]` with `fixed=fixed` and `moving=moving`.
- Do not reverse transform lists unless you have manually derived and validated the chain.
- Set `whichtoinvert` explicitly when matrix files are involved. A matrix can be inverted at apply time; a warp field cannot.
- Remember that the same affine `.mat` can appear in both forward and inverse registration lists. Inversion is controlled by `whichtoinvert`, not by a separate inverse `.mat` file.
- If composing transforms from multiple registrations, validate the chain with one small image or known point before processing a full dataset.

## Points Move in the Opposite Direction

Symptoms: image warping looks correct, but landmarks move away from expected fixed-space positions.

Checks and fixes:

- `apply_transforms_to_points` directly maps physical coordinates, while image resampling maps output samples backward into the moving image.
- For moving landmarks into fixed coordinates, start with `tx["invtransforms"]` and set `whichtoinvert=True` for affine `.mat` files in that list.
- For fixed landmarks into moving coordinates, test `tx["fwdtransforms"]` on one known point before batch use.
- Use a pandas `DataFrame` with columns `x`, `y`, optionally `z`, and optionally `t`; extra columns are preserved.
- Convert voxel indices to physical coordinates before applying transforms.

## Dimension or Physical-Space Mismatch

Common failures include `Fixed and moving image dimensions are not the same`, point dimension errors, transform component errors, or mask-domain mistakes.

Checks and fixes:

- `fixed.dimension` and `moving.dimension` must match for `ants.registration`.
- Registration masks must be in the correct image domains: `mask` in fixed space and `moving_mask` in moving space.
- Mask dimensions and physical metadata must match their corresponding images.
- `apply_transforms_to_points(dim, ...)` must match the point coordinate columns and transform dimensionality.
- Displacement-field images need one vector component per spatial dimension.
- `fsl2antstransform` requires 3D reference and moving images.
- Use image-core workflows to inspect or repair `origin`, `spacing`, `direction`, `shape`, and pixel/component metadata before registration.

## Interpolator or `imagetype` Problems

Symptoms: unsupported interpolator errors, fractional labels, failed 4D-to-3D time-series transforms, or vector/tensor orientation issues.

Checks and fixes:

- Use exact interpolator strings: `linear`, `nearestNeighbor`, `genericLabel`, `gaussian`, `bSpline`, or one of the supported sinc interpolators.
- For labels and segmentations, use `genericLabel` or `nearestNeighbor`; do not use `linear` unless you plan to re-threshold/relabel.
- For masks, use `nearestNeighbor` or re-threshold after interpolation.
- When moving is 4D and fixed is 3D, call `ants.apply_transforms(..., imagetype=3)`.
- For vector images and tensor images, use `imagetype=1` or `imagetype=2` so ANTsPy reorients components correctly.
- For physical displacement fields, use `imagetype=6` when applying a transform to the field itself.

## Transform File Is Missing

Symptoms: `Transform ... does not exist`, `read_transform` reports a missing filename, or a later step cannot find registration outputs.

Checks and fixes:

- `ants.registration(..., outprefix='')` uses a temporary prefix. Set `outprefix` to a task-owned writable prefix if you need transform files later.
- Keep the directory containing transform files alive until all `apply_transforms`, Jacobian, composition, or IO steps finish.
- `apply_transforms` checks that every transform path exists before running image resampling.
- `read_transform` expands `~` but still requires an existing file.
- If using `compose`, pass a writable prefix or `.h5` filename and verify the returned filename is not `None`.
- If using `write_composite_transform=True`, expect `fwdtransforms` and `invtransforms` to be composite filenames instead of ordinary stage-wise lists.

## Registration Is Too Slow or Uses Too Much Memory

Symptoms: long runtime, high memory use, or a task hangs on default `SyN`.

Checks and fixes:

- Start with `Translation`, `QuickRigid`, `Rigid`, or `AffineFast` to confirm image domains and transform directions.
- Use `antsRegistrationSyNQuick[...]` before full `SyN` when a nonlinear transform is needed quickly.
- Lower `reg_iterations`, `aff_iterations`, and image resolution for debugging; increase only after correctness is established.
- Use masks to constrain metrics, but verify mask quality first because a bad mask can damage convergence.
- Keep `singleprecision=True` unless double precision is required.
- Prefer smaller cropped/resampled images for smoke tests; route preprocessing details to image-ops-math.

## Registration Raises Argument Errors

Checks and fixes:

- `fixed` and `moving` must be `ANTsImage` objects, not NumPy arrays or filenames.
- Replace NaNs before registration; ANTsPy rejects fixed or moving images containing NaNs.
- `type_of_transform` must be a supported name. Use transform-types guidance when choosing a family.
- If one affine schedule argument is an integer, `aff_iterations`, `aff_shrink_factors`, and `aff_smoothing_sigmas` must all be integers.
- If affine schedule arguments are tuples, their lengths must match.
- `multivariate_extras` entries must each contain five values: metric name, fixed image, moving image, weight, and sampling parameter.
- `restrict_transformation` works only when there are no preceding transforms.

## Jacobian or Deformation Gradient Fails

Checks and fixes:

- Use a deformation warp file or vector displacement-field image, not a pure affine `.mat`, for local Jacobian/deformation-gradient diagnostics.
- If registration produced only affine transforms, there is no nonlinear warp to diagnose.
- For `deformation_gradient(py_based=True)`, pass an in-memory `ANTsImage` warp, not a filename.
- For the non-Python backend path, filenames may be written temporarily; keep inputs accessible until the function returns.
- Check that vector field component count equals spatial dimension before converting it to a transform.

## Motion Correction or Template Building Surprises

Checks and fixes:

- `motion_correction` expects a time-series image, usually 4D, and registers frames to `fixed` or a mean image.
- Use `BOLDRigid` or another rigid/affine transform for motion correction before trying deformable options.
- `build_template` runs registration internally for every image and iteration; set `iterations=1` and a cheap `type_of_transform` for tests.
- If you pass `output_dir` to `build_template`, use a task-owned writable directory and expect intermediate transform files there.
- If `output_dir` is omitted, intermediate files are temporary and should not be referenced later.

## Transform Object IO and FSL Conversion

Checks and fixes:

- `write_transform` requires an `ANTsTransform`, not a transform filename or numeric matrix.
- `create_ants_transform` supports dimensions 2 through 4, but some transform types force 2D or 3D.
- `precision` must be `float` or `double`.
- `fsl2antstransform` expects a 4x4 matrix and 3D `reference` and `moving` images; ANTsPy clones non-float images to float internally.
- When composing in-memory transforms, all transforms must have the same precision and dimension.
