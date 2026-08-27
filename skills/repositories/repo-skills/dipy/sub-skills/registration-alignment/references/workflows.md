# Registration And Alignment Workflows

These recipes are self-contained operational guides for Dipy registration tasks. They avoid assuming optional visualization packages and assume data IO has already been planned with `../../io-data/` when files, headers, b-values/b-vectors, or tractogram references matter.

## Choose The Alignment Family

| Situation | Prefer | Why |
| --- | --- | --- |
| Voxel sizes differ but anatomical space is already compatible | Reslice/resample | Changes grid resolution without estimating anatomical correspondence. |
| Images differ by global position, rotation, scale, shear, or scanner-space mismatch | Affine registration | Estimates an interpretable 4x4 transform and is faster/safer than nonlinear warping. |
| Images are already roughly aligned but anatomy differs nonlinearly | SyN registration | Estimates smooth diffeomorphic deformation after affine prealignment. |
| A known transform already exists | Apply transform | Separates estimation from resampling and keeps provenance clear. |
| 4D DWI volumes are internally misaligned by subject motion | Motion correction | Registers each volume to a b0/reference using affine machinery. |
| Bundles/tractograms are the object being aligned | SLR or BundleWarp | Operates in streamline coordinate space rather than voxel grid space. |

## Reslice A Tiny Or Real Image

1. Load the image data, affine, and voxel sizes through the IO skill or a trusted in-memory source.
2. Decide `new_zooms` deliberately. Smaller voxel sizes increase array shape and memory; larger voxel sizes lose detail.
3. Pick interpolation by data type: `order=1` for scalar images, `order=0` for labels/masks, optional Lanczos strings for image-quality experiments.
4. Run `reslice(data, affine, zooms, new_zooms, order=..., mode=..., num_processes=...)`.
5. Validate `data2.shape[:3]`, the new affine diagonal/voxel sizes, and that 4D inputs preserve `shape[-1]`.
6. Save with the updated affine; route NIfTI header details to `../../io-data/`.

CLI pattern:

```bash
dipy_reslice input.nii.gz 2.0 2.0 2.0 --out_dir reslice_out --out_resliced resliced.nii.gz
```

Notes:

- If `dipy_reslice` is called without `new_vox_size`, it auto-computes an isotropic target from the original voxel sizes and `vox_factor`, with safeguards to avoid targets above 2 mm.
- If input voxel sizes already match the target, the workflow skips reslicing and returns the original path.

## Estimate An Affine Image Transform

1. Identify the static/reference image and moving/source image. The moving image is resampled into static space.
2. If inputs are arrays, provide `moving_affine` and `static_affine`; if inputs are NIfTI objects or paths, Dipy can read affines from them.
3. Choose a transform pipeline:
   - `center_of_mass`: rough translation from mass centers only.
   - `translation`: center of mass plus translation.
   - `rigid`: translation and rotation.
   - `rigid_isoscaling` or `rigid_scaling`: rigid plus scale terms.
   - `affine`: full translation, rotation, scale, and shear.
4. Use coarse-to-fine settings. For quick smoke tests, shrink `level_iters`; for production, use defaults or domain-specific tuning.
5. Consider masks when background dominates mutual information.
6. Validate the output by checking shape equals static shape, affine matrix is finite `(4, 4)`, determinant is plausible, and transformed landmarks/overlaps improve.

Python pattern:

```python
from dipy.align import affine_registration

moved, matrix = affine_registration(
    moving,
    static,
    moving_affine=moving_affine,
    static_affine=static_affine,
    pipeline=["center_of_mass", "translation", "rigid", "affine"],
    level_iters=[1000, 500, 100],
    sigmas=[3, 1, 0],
    factors=[4, 2, 1],
)
```

CLI pattern:

```bash
dipy_align_affine static.nii.gz moving.nii.gz --transform affine --out_dir affine_out --out_affine affine.txt
```

## Decide Affine Versus SyN For Multimodal Alignment

Use affine first when images are from different modalities or contrasts but should share global brain geometry. Mutual-information affine registration is usually the safer first pass because it is interpretable and less likely to invent local deformation.

Add SyN when all of these are true:

- A global transform is not enough for the scientific question.
- Images are already roughly aligned, either from scanner geometry or a saved affine prealignment.
- Nonlinear deformation is anatomically plausible for the tissue and population.
- You can validate deformation magnitude and inverse consistency without relying solely on screenshots.

For multimodal SyN, consider `EM` when intensity relationships are complex, `CC` for similar local contrast, and `SSD` mostly for monomodal intensity-matched data.

## Run SyN Registration And Save A Mapping

1. Start from aligned/cropped static and moving 2D or 3D images.
2. If available, estimate an affine prealignment first and pass it as `prealign`.
3. Select metric and metric-specific options:
   - `CC`: `sigma_diff`, `radius`.
   - `SSD`: `smooth`, `inner_iter`, `step_type`.
   - `EM`: `smooth`, `inner_iter`, `q_levels`, `double_gradient`, `step_type`.
4. Keep `level_iters` small for probes and increase only after behavior is validated.
5. Save both warped output and displacement field if downstream application is needed.

Python pattern:

```python
from dipy.align import syn_registration, write_mapping

warped, mapping = syn_registration(
    moving,
    static,
    moving_affine=moving_affine,
    static_affine=static_affine,
    metric="CC",
    level_iters=[10, 10, 5],
    prealign=affine_matrix,
)
write_mapping(mapping, "displacement_field.nii.gz")
```

CLI pattern:

```bash
dipy_align_syn static.nii.gz moving.nii.gz --prealign_file affine.txt --metric cc --out_dir syn_out --out_field displacement_field.nii.gz
```

## Apply A Saved Transform

1. Confirm transform type: affine matrices are text files; diffeomorphic fields are NIfTI files with shape `(X, Y, Z, 3, 2)`.
2. Use the same static/reference grid used when the transform was estimated.
3. Use `nearest` interpolation for label maps and `linear` for scalar images.
4. Validate output shape equals the static image shape and output affine is the static affine.

CLI pattern:

```bash
dipy_apply_transform static.nii.gz moving.nii.gz affine.txt --transform_type affine --interpolation linear --out_dir applied_out
```

For diffeomorphic fields:

```bash
dipy_apply_transform static.nii.gz moving.nii.gz displacement_field.nii.gz --transform_type diffeomorphic --interpolation linear --out_dir applied_out
```

## Correct DWI Between-Volume Motion

1. Route b-values/b-vectors and `GradientTable` validation to `../../io-data/`.
2. Confirm the DWI is 4D and the gradient count matches the last image dimension.
3. Set `b0_threshold` high enough to identify b0 volumes; a too-low threshold can trigger warnings and poor reference selection.
4. Run motion correction on a crop or small volume subset for runtime estimation when the dataset is large.
5. Validate corrected data shape equals input shape and that the returned affine stack has one transform per volume.

Python pattern:

```python
from dipy.align import motion_correction

corrected_img, affines = motion_correction(data, gtab, affine=affine, level_iters=[1000, 500, 100])
```

CLI pattern:

```bash
dipy_correct_motion dwi.nii.gz dwi.bval dwi.bvec --out_dir motion_out --out_moved moved.nii.gz --out_affine affine.txt
```

## Run Streamline Linear Registration

1. Route tractogram format, reference, `Space`, `Origin`, and bbox decisions to `../../io-data/`.
2. Ensure static and moving streamlines represent comparable anatomy and coordinate units.
3. Resample streamlines to a fixed point count for stable metrics.
4. Choose `x0`: `rigid` for conservative pose alignment, `similarity` or `affine` when scale/shear is expected.
5. Use SLR with QBX when full tractograms are large; registration is estimated on cluster centroids.
6. Validate that moved streamlines overlap static streamlines better and the matrix is finite.

Python pattern:

```python
from dipy.align import streamline_registration

aligned_streamlines, matrix = streamline_registration(moving_streamlines, static_streamlines, n_points=100)
```

CLI pattern:

```bash
dipy_slr static.trx moving.trx --x0 affine --nb_pts 20 --out_dir slr_out --bbox_valid_check false
```

## Run BundleWarp Carefully

1. Start from cleaned, anatomically corresponding static and moving bundles.
2. Prefer SLR/affine prealignment before nonlinear bundle deformation.
3. Use default or moderate `alpha` first. Lower `alpha` means stronger deformation; values `<=0.01` can drastically alter anatomy.
4. Preserve outputs separately: linearly moved bundle, nonlinearly moved bundle, warp transforms, kernel, distance matrix, and matched pairs.
5. Validate deformation magnitudes and matched pairs numerically before interpreting downstream tractometry.

CLI pattern:

```bash
dipy_bundlewarp static.trx moving.trx --alpha 0.5 --out_dir bundlewarp_out
```

## Optional QA Without Hard Plot Dependencies

- Numeric checks: shape, affine, transform matrix determinant, finite displacement fields, overlap metrics, landmark distances, bundle distance matrices, and streamline lengths.
- Visual checks: `dipy.viz.regtools.overlay_slices` can save overlays when plotting dependencies are installed, but do not require it in minimal environments.
- For command-line work, use small output directories and avoid overwriting inputs unless the user explicitly requests `--force` behavior.
