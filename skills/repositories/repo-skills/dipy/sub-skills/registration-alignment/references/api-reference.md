# Registration And Alignment API Reference

This reference summarizes Dipy runtime APIs for image reslicing, affine/SyN registration, transform application, motion correction, streamline linear registration, and BundleWarp. It assumes arrays/files are already available locally; route file loading, headers, gradients, and tractogram reference details to `../../io-data/`.

## Image Reslicing

| Need | API | Key parameters | Outputs and notes |
| --- | --- | --- | --- |
| Resample image arrays to new voxel sizes | `dipy.align.reslice.reslice(data, affine, zooms, new_zooms, *, order=1, mode="constant", cval=0, num_processes=1, new_shape=None)` | `data` is 3D or 4D; `zooms` and `new_zooms` are length-3 voxel sizes; `order` can be spline `0..5`, `"lanczos"`, `"lanczos2"`, or `"lanczos3"`; `mode` controls outside-boundary fill | Returns `(data2, affine2)`. Shape is computed as `round(zooms / new_zooms * data.shape[:3])` unless `new_shape` is supplied. 4D input preserves the last dimension. |
| Preserve labels during reslice | same `reslice` API | Use `order=0` and usually `mode="nearest"` or `mode="constant"` | Avoid linear/spline interpolation for integer labels or masks. |
| Parallelize 4D reslice | same `reslice` API | `num_processes=1` default, `<0` uses an automatic worker count, `0` raises an error; ignored for Lanczos modes | Validate memory before large 4D jobs; each volume is resampled independently. |

## Affine Image Registration

| Need | API | Key parameters | Outputs and notes |
| --- | --- | --- | --- |
| High-level affine pipeline | `dipy.align.affine_registration(moving, static, *, moving_affine=None, static_affine=None, pipeline=None, starting_affine=None, metric="MI", level_iters=None, sigmas=None, factors=None, ret_metric=False, moving_mask=None, static_mask=None, optimizer_options=None, optimizer_method=None, **metric_kwargs)` | `moving` and `static` can be arrays, NIfTI images, or paths; arrays require affines. Default pipeline is `center_of_mass`, `translation`, `rigid`, `affine`. Default pyramid settings are `level_iters=[1000, 500, 100]`, `sigmas=[3, 1, 0]`, `factors=[4, 2, 1]`. | Returns `(resampled, final_affine)` or `(resampled, final_affine, xopt, fopt)` when `ret_metric=True`. The resampled image is in static space. |
| Single-step helpers | `dipy.align.center_of_mass`, `translation`, `rigid`, `rigid_isoscaling`, `rigid_scaling`, `affine` | Same key arguments as `affine_registration`; each helper fixes a one-step pipeline | Center of mass cannot return an optimization metric. |
| Low-level registration object | `dipy.align.imaffine.AffineRegistration(*, metric=None, level_iters=None, sigmas=None, factors=None, method="L-BFGS-B", ss_sigma_factor=None, options=None, verbosity=STATUS)` | Pair with transform classes from `dipy.align.transforms` and a similarity metric such as mutual information | Use only when the convenience pipeline is too restrictive. |
| Apply an affine to image data | `dipy.align.imaffine.AffineMap(affine, domain_grid_shape, domain_grid2world, codomain_grid_shape, codomain_grid2world).transform(moving, interpolation="linear")` | Domain is the static/reference grid; codomain is the moving/source grid | CLI `dipy_apply_transform --transform_type affine` wraps this pattern for saved matrices. |

## SyN And Diffeomorphic Registration

| Need | API | Key parameters | Outputs and notes |
| --- | --- | --- | --- |
| High-level SyN registration | `dipy.align.syn_registration(moving, static, *, moving_affine=None, static_affine=None, step_length=0.25, metric="CC", dim=3, level_iters=None, prealign=None, **metric_kwargs)` | Metrics: `CC`, `SSD`, or `EM`; default `level_iters=[10, 10, 5]`; `prealign` can seed SyN with an affine matrix | Returns `(warped_moving, mapping)`, where `mapping` is a `DiffeomorphicMap` that can transform data. |
| Low-level SyN optimizer | `dipy.align.imwarp.SymmetricDiffeomorphicRegistration(metric, *, level_iters=None, step_length=0.25, ss_sigma_factor=0.2, opt_tol=1e-05, inv_iter=20, inv_tol=0.001, callback=None)` | Metric objects include `CCMetric(dim, sigma_diff=..., radius=...)`, `SSDMetric(dim, smooth=..., inner_iter=..., step_type=...)`, and `EMMetric(dim, ...)` | Use for custom callbacks or metric options. `optimize(static, moving, static_grid2world=..., moving_grid2world=..., prealign=...)` returns a mapping. |
| Save/read SyN mapping | `dipy.align.write_mapping(mapping, fname)` and `dipy.align.read_mapping(disp, domain_img, codomain_img, *, prealign=None)` | Stored displacement field shape is `(X, Y, Z, 3, 2)`, with forward and backward fields in the last axis | Useful when separating registration estimation from later transform application. |
| Register DWI b0 to template | `dipy.align.register_dwi_to_template(dwi, gtab, *, dwi_affine=None, template=None, template_affine=None, reg_method="syn", **reg_kwargs)` | `gtab` can be a `GradientTable` or `(bvals, bvecs)` paths; uses mean b0 volumes | Returns warped b0 plus a SyN mapping or affine matrix. This assumes the DWI series is already internally registered. |

## Motion Correction

| Need | API | Key parameters | Outputs and notes |
| --- | --- | --- | --- |
| Register a 4D series to a reference volume | `dipy.align.register_series(series, ref, *, pipeline=None, series_affine=None, ref_affine=None, level_iters=None, sigmas=None, factors=None, static_mask=None)` | `ref` is usually a b0 index or reference image; affine settings follow affine registration | Returns a registered NIfTI-like image and one affine per volume. |
| DWI between-volume correction | `dipy.align.motion_correction(data, gtab, *, affine=None, b0_ref=0, pipeline=None, level_iters=None, sigmas=None, factors=None, static_mask=None)` | Requires 4D data, gradient table, and affine when `data` is an array | Returns corrected image data as a NIfTI object plus registration affines. |

## Streamline And Bundle Registration

| Need | API | Key parameters | Outputs and notes |
| --- | --- | --- | --- |
| Streamline linear registration object | `dipy.align.streamlinear.StreamlineLinearRegistration(*, metric=None, x0="rigid", method="L-BFGS-B", bounds=None, verbose=False, options=None, evolution=False, num_threads=None)` | `x0` can be a preset/model or parameter vector; default bounds constrain translation/rotation/scale/shear | Call `optimize(static, moving)` on streamlines with comparable anatomy and coordinate space. |
| High-level streamline registration | `dipy.align.streamline_registration(moving, static, *, n_points=100, native_resampled=False)` | Accepts streamline sequences or tractogram paths; resamples streamlines to `n_points` internally unless native resampling is requested | Returns aligned streamlines and the matrix that maps moving toward static. Route tractogram loading/saving details to `../../io-data/`. |
| SLR with QuickBundlesX | `dipy.align.streamlinear.slr_with_qbx(static, moving, *, x0="affine", rm_small_clusters=50, greater_than=50, less_than=250, qbx_thr=(40, 30, 20, 15), progressive=True, nb_pts=20, select_random=None, rng=None, verbose=False, num_threads=None)` | Filters short/long streamlines, clusters with QBX, then runs SLR on centroids | Returns moved streamlines, affine, static centroids, and moving centroids. CLI `dipy_slr` wraps this. |
| BundleWarp nonlinear bundle registration | `dipy.align.streamwarp.bundlewarp(static, moving, *, dist=None, alpha=0.5, beta=20, max_iter=15, affine=True)` | `alpha` controls deformation strength; lower values deform more. `alpha<=0.01` warns because it can strongly alter anatomy. | Returns deformed bundle, linearly moved bundle, distance matrix, matched pairs, and warp metadata. |
| BundleWarp QA arrays | `bundlewarp_vector_filed(moving_aligned, deformed_bundle)` and `bundlewarp_shape_analysis(..., no_disks=10, plotting=False)` | Plotting is optional and depends on visualization packages | Shape analysis can produce per-segment displacement summaries; downstream tractometry belongs in `../../tracking-segmentation/`. |

## Optional Visualization QA

| Need | API | Notes |
| --- | --- | --- |
| Static/moving slice overlay | `dipy.viz.regtools.overlay_slices(L, R, *, slice_index=None, slice_type=1, ltitle="Left", rtitle="Right", fname=None, **fig_kwargs)` | Requires plotting dependencies such as matplotlib. In minimal environments, treat visual QA as optional and validate numerically first. |

## CLI Entry Points Owned Here

| CLI | Flow | Typical purpose | Primary outputs |
| --- | --- | --- | --- |
| `dipy_reslice` | `ResliceFlow` | Resample NIfTI volumes to manual or auto-computed voxel sizes | `resliced.nii.gz` or original path if voxel size already matches |
| `dipy_align_affine` | `ImageRegistrationFlow` | Center of mass, translation, rigid, scaling, or affine image registration | `moved.nii.gz`, `affine.txt`, optional `quality_metric.txt` |
| `dipy_align_syn` | `SynRegistrationFlow` | Diffeomorphic SyN image registration | `warped_moved.nii.gz`, `inc_static.nii.gz`, `displacement_field.nii.gz` |
| `dipy_apply_transform` | `ApplyTransformFlow` | Apply affine or diffeomorphic transform to one or more images | `transformed.nii.gz` |
| `dipy_correct_motion` | `MotionCorrectionFlow` | Between-volume DWI motion correction | `moved.nii.gz`, `affine.txt` with one affine per volume |
| `dipy_slr` | `SlrWithQbxFlow` | Streamline linear registration using QBX centroids | moved tractogram, affine matrix, centroid tractograms |
| `dipy_bundlewarp` | `BundleWarpFlow` | Nonlinear bundle registration | linear/nonlinear moved tractograms plus warp, kernel, distance, and match arrays |

Use `../../cli-workflows/` for parser mechanics and `--help` discovery, but keep scientific parameter decisions in this sub-skill.
