# Registration and Transform API Reference

The public APIs below are available from `import ants`. Signatures were verified against the `antspyx` public package in the 0.6.x line and cross-checked with the current ANTsPy source layout.

## Image Registration APIs

| API | Verified signature | Return and notes |
| --- | --- | --- |
| `ants.registration` | `registration(fixed, moving, type_of_transform='SyN', initial_transform=None, outprefix='', mask=None, moving_mask=None, mask_all_stages=False, grad_step=0.2, flow_sigma=3, total_sigma=0, aff_metric='mattes', aff_sampling=32, aff_random_sampling_rate=0.2, syn_metric='mattes', syn_sampling=32, reg_iterations=(40, 20, 0), aff_iterations=(2100, 1200, 1200, 10), aff_shrink_factors=(6, 4, 2, 1), aff_smoothing_sigmas=(3, 2, 1, 0), write_composite_transform=False, verbose=False, multivariate_extras=None, restrict_transformation=None, smoothing_in_mm=False, singleprecision=True, use_legacy_histogram_matching=False, **kwargs)` | Registers `moving` to `fixed`; returns a dict described below. |
| `ants.motion_correction` | `motion_correction(image, fixed=None, type_of_transform='BOLDRigid', mask=None, fdOffset=50, outprefix='', verbose=False, **kwargs)` | Motion-corrects a time-series image, typically 4D, by registering each frame to `fixed` or a mean image. |
| `ants.label_image_registration` | `label_image_registration(fixed_label_images, moving_label_images, fixed_intensity_images=None, moving_intensity_images=None, fixed_mask=None, moving_mask=None, initial_transforms='affine', type_of_deformable_transform='antsRegistrationSyNQuick[so]', label_image_weighting=1.0, output_prefix='', verbose=False)` | Pairwise registration driven by label images, optionally with intensity images. Use segmentation-labels for label analysis. |
| `ants.affine_initializer` | `affine_initializer(fixed_image, moving_image, search_factor=20, radian_fraction=0.1, use_principal_axis=False, local_search_iterations=10, mask=None, txfn=None)` | Writes and returns an affine `.mat` filename that can initialize later registration. |
| `ants.build_template` | `build_template(initial_template=None, image_list=None, iterations=3, gradient_step=0.2, blending_weight=0.75, weights=None, useNoRigid=True, output_dir=None, **kwargs)` | Iteratively registers images to an evolving template and returns an `ANTsImage`. Extra kwargs pass through to `ants.registration`. |

## `ants.registration` Return Dict

| Key | Meaning |
| --- | --- |
| `warpedmovout` | The moving image resampled into fixed image space. |
| `warpedfixout` | The fixed image resampled into moving image space. |
| `fwdtransforms` | Transform filename list for moving-to-fixed image warping with `ants.apply_transforms`. If `write_composite_transform=True`, this can be a composite `.h5` filename rather than a list. |
| `invtransforms` | Transform filename list for fixed-to-moving image warping. For point mapping, this is commonly the starting list for moving-to-fixed points when affine inversion flags are set correctly. |
| `velocityfield` | Present for time-varying registrations that write velocity-field outputs. |

The same affine `.mat` file can appear in both `fwdtransforms` and `invtransforms`. ANTsPy does not need a second matrix file; the matrix is inverted at application time by `whichtoinvert`.

If `outprefix=''`, ANTsPy uses a temporary prefix for transform files. Set an explicit writable `outprefix` when transform files must survive beyond the current operation.

## Applying Transform Lists

| API | Verified signature | Use |
| --- | --- | --- |
| `ants.apply_transforms` | `apply_transforms(fixed, moving, transformlist, interpolator='linear', imagetype=0, whichtoinvert=None, compose=None, defaultvalue=0, singleprecision=False, verbose=False, **kwargs)` | Resample `moving` into the domain of `fixed`; returns an `ANTsImage`, or a composite transform filename when `compose` is set. |
| `ants.apply_transforms_to_points` | `apply_transforms_to_points(dim, points, transformlist, whichtoinvert=None, verbose=False)` | Apply transform files to a pandas `DataFrame` of physical-space point coordinates with columns `x`, `y`, optionally `z`, and optionally `t`. |

Supported `apply_transforms` interpolators are exact strings: `linear`, `nearestNeighbor`, `multiLabel`, `gaussian`, `bSpline`, `cosineWindowedSinc`, `welchWindowedSinc`, `hammingWindowedSinc`, `lanczosWindowedSinc`, and `genericLabel`. Prefer `genericLabel` or `nearestNeighbor` for label images; `multiLabel` remains available but is deprecated in favor of `genericLabel`.

`imagetype` values are `0` scalar, `1` spatial vector in index coordinates, `2` diffusion tensor in index coordinates, `3` time series, `4` multi-channel image, and `6` spatial vector in physical coordinates such as a displacement field. Use `imagetype=3` when transforming a 4D time series into a 3D reference.

`whichtoinvert` must match the transform-list length. ANTsPy infers `(True, False)` only for a two-item list where the first item is a `.mat` file and the second is not; otherwise it defaults to all `False`. A `True` flag is valid only for matrix transform files.

## Transform Objects and IO

| API | Signature | Use |
| --- | --- | --- |
| `ants.create_ants_transform` | `create_ants_transform(transform_type='AffineTransform', precision='float', dimension=3, matrix=None, offset=None, center=None, translation=None, parameters=None, fixed_parameters=None, displacement_field=None, supported_types=False)` | Create an `ANTsTransform`; pass `supported_types=True` to inspect supported transform-object names. |
| `ants.new_ants_transform` | `new_ants_transform(precision='float', dimension=3, transform_type='AffineTransform', parameters=None, fixed_parameters=None)` | Low-level constructor; prefer `create_ants_transform` for user-facing code. |
| `ants.read_transform` | `read_transform(filename, precision='float')` | Read `.mat`, composite, or displacement-field transform files into an `ANTsTransform`. `.nii` and `.nii.gz` files are read as displacement fields. |
| `ants.write_transform` | `write_transform(transform, filename)` | Write an `ANTsTransform` to disk. Affine transforms conventionally use `.mat`. |
| `ants.transform_from_displacement_field` | `transform_from_displacement_field(field)` | Convert a vector displacement-field `ANTsImage` to a `DisplacementFieldTransform`. Components must equal spatial dimension. |
| `ants.transform_to_displacement_field` | `transform_to_displacement_field(xfrm, ref)` | Convert a displacement-field transform back to a vector displacement-field image on reference domain `ref`. |
| `ants.fsl2antstransform` | `fsl2antstransform(matrix, reference, moving)` | Convert an FSL 4x4 linear matrix to an ANTs affine transform using 3D reference and moving images. |

Supported matrix-offset transform object types include `AffineTransform`, `CenteredAffineTransform`, `Euler2DTransform`, `Euler3DTransform`, `Rigid2DTransform`, `Rigid3DTransform`, `QuaternionRigidTransform`, `Similarity2DTransform`, `Similarity3DTransform`, `CenteredSimilarity2DTransform`, `CenteredRigid2DTransform`, and `CenteredEuler3DTransform`. `DisplacementFieldTransform` is supported through a displacement-field image.

`ANTsTransform` instances expose `.parameters`, `.fixed_parameters`, `.invert()`, `.apply_to_point(point)`, `.apply_to_vector(vector)`, and `.apply_to_image(image, reference=None, interpolation='linear')`. Functional wrappers include `ants.apply_ants_transform`, `ants.apply_ants_transform_to_point`, `ants.apply_ants_transform_to_vector`, `ants.apply_ants_transform_to_image`, `ants.invert_ants_transform`, and `ants.compose_ants_transforms`.

## Displacement, Jacobian, and Grid Helpers

| API | Verified signature | Use |
| --- | --- | --- |
| `ants.average_affine_transform` | `average_affine_transform(transformlist, referencetransform=None)` | Average affine transform files and return an `ANTsTransform`. |
| `ants.average_affine_transform_no_rigid` | `average_affine_transform_no_rigid(transformlist, referencetransform=None)` | Average affine transforms while excluding rigid components. |
| `ants.compose_displacement_fields` | `compose_displacement_fields(displacement_field, warping_field)` | Compose two displacement-field `ANTsImage` objects. |
| `ants.invert_displacement_field` | `invert_displacement_field(displacement_field, inverse_field_initial_estimate, maximum_number_of_iterations=20, mean_error_tolerance_threshold=0.001, max_error_tolerance_threshold=0.1, enforce_boundary_condition=True)` | Iteratively invert a displacement field from an initial inverse estimate. |
| `ants.integrate_velocity_field` | `integrate_velocity_field(velocity_field, lower_integration_bound=0.0, upper_integration_bound=1.0, number_of_integration_steps=10)` | Integrate a time-varying velocity field over a time interval. |
| `ants.create_jacobian_determinant_image` | `create_jacobian_determinant_image(domain_image, tx, do_log=False, geom=False)` | Compute a Jacobian determinant image from a deformation transform file or displacement field. |
| `ants.deformation_gradient` | `deformation_gradient(warp_image, to_rotation=False, to_inverse_rotation=False, py_based=False)` | Compute deformation gradients, or local rotations via polar decomposition, from a warp image. |
| `ants.create_warped_grid` | `create_warped_grid(image, grid_step=10, grid_width=2, grid_directions=(True, True), fixed_reference_image=None, transform=None, foreground=1, background=0)` | Build a grid image and optionally warp it through a transform list. |
| `ants.simulate_displacement_field` | `simulate_displacement_field(domain_image, field_type='bspline', number_of_random_points=1000, sd_noise=10.0, enforce_stationary_boundary=True, number_of_fitting_levels=4, mesh_size=1, sd_smoothing=4.0)` | Simulate a B-spline or exponential displacement-field image on a domain. |
| `ants.fit_bspline_displacement_field` | `fit_bspline_displacement_field(displacement_field=None, displacement_weight_image=None, displacement_origins=None, displacements=None, displacement_weights=None, origin=None, spacing=None, size=None, direction=None, number_of_fitting_levels=4, mesh_size=1, spline_order=3, enforce_stationary_boundary=True, estimate_inverse=False, rasterize_points=False)` | Fit/smooth a displacement field from a dense field, scattered point displacements, or both. |
| `ants.fit_bspline_object_to_scattered_data` | `fit_bspline_object_to_scattered_data(scattered_data, parametric_data, parametric_domain_origin, parametric_domain_spacing, parametric_domain_size, is_parametric_dimension_closed=None, data_weights=None, number_of_fitting_levels=4, mesh_size=1, spline_order=3)` | Fit a B-spline curve, scalar field, displacement field, or velocity-field-like object from scattered data. |
| `ants.fit_thin_plate_spline_displacement_field` | `fit_thin_plate_spline_displacement_field(displacement_origins=None, displacements=None, origin=None, spacing=None, size=None, direction=None)` | Fit a thin-plate spline displacement field from point displacements. |

## Landmark Transform Helpers

| API | Verified signature | Return and notes |
| --- | --- | --- |
| `ants.fit_transform_to_paired_points` | `fit_transform_to_paired_points(moving_points, fixed_points, transform_type='affine', regularization=1e-06, domain_image=None, number_of_fitting_levels=4, mesh_size=1, spline_order=3, enforce_stationary_boundary=True, displacement_weights=None, number_of_compositions=10, composition_step_size=0.5, sigma=0.0, convergence_threshold=1e-06, number_of_time_steps=2, number_of_integration_steps=100, rasterize_points=False, verbose=False)` | Estimates `rigid`, `similarity`, `affine`, `bspline`, `tps`, `diffeo`, `syn`, or time-varying transforms from paired physical-space landmarks. Nonlinear modes require `domain_image`. `syn` and time-varying modes return dicts of forward/inverse components. |
| `ants.fit_time_varying_transform_to_point_sets` | `fit_time_varying_transform_to_point_sets(point_sets, time_points=None, initial_velocity_field=None, number_of_time_steps=None, domain_image=None, number_of_fitting_levels=4, mesh_size=1, spline_order=3, displacement_weights=None, number_of_compositions=10, composition_step_size=0.5, number_of_integration_steps=100, sigma=0.0, convergence_threshold=1e-06, rasterize_points=False, verbose=False)` | Estimates a time-varying transform from three or more corresponding point sets and returns `forward_transform`, `inverse_transform`, and `velocity_field`. |

Landmark arrays and point DataFrames must be in physical coordinates, not voxel indices. Validate direction on one known point before applying a fitted landmark transform to a full point set.
