# Registration and Transform Workflows

These recipes assume images have already been loaded or created as `ANTsImage` objects. Use image-core for IO and metadata repair, image-ops-math for preprocessing/masks/resampling, and segmentation-labels for label-specific downstream analysis.

## Fast Deterministic Rigid or Affine Registration

Use a cheap transform first to validate domains, metric behavior, output keys, and transform direction.

```python
import ants

tx = ants.registration(
    fixed=fixed,
    moving=moving,
    type_of_transform="AffineFast",
    aff_iterations=(40, 0, 0, 0),
    aff_shrink_factors=(1, 1, 1, 1),
    aff_smoothing_sigmas=(0, 0, 0, 0),
    aff_random_sampling_rate=1.0,
    singleprecision=True,
)

required = {"warpedmovout", "warpedfixout", "fwdtransforms", "invtransforms"}
missing = required.difference(tx)
if missing:
    raise RuntimeError(f"registration output missing keys: {sorted(missing)}")
```

Validation checks:

```python
warped = ants.apply_transforms(
    fixed=fixed,
    moving=moving,
    transformlist=tx["fwdtransforms"],
    interpolator="linear",
)
if warped.shape != fixed.shape:
    raise RuntimeError("warped image did not land in fixed image shape")
```

For a smoke test, prefer `Translation`, `QuickRigid`, `Rigid`, or `AffineFast`. Do not start default `SyN` until image domains, masks, and transform directions are correct.

## Bounded Nonlinear Registration

When nonlinear deformation is required, use a quick preset or explicit short iteration schedule first:

```python
tx = ants.registration(
    fixed=fixed,
    moving=moving,
    type_of_transform="antsRegistrationSyNQuick[s]",
    reg_iterations=(40, 20, 0),
    singleprecision=True,
)
warped = tx["warpedmovout"]
```

For deformable-only refinement after a separately estimated affine:

```python
affine = ants.registration(fixed, moving, type_of_transform="AffineFast")
syn = ants.registration(
    fixed=fixed,
    moving=moving,
    type_of_transform="SyNOnly",
    initial_transform=affine["fwdtransforms"][0],
    reg_iterations=(40, 20, 0),
)
```

If deterministic mode is enabled, use `antsRegistrationSyNQuickRepro[...]` or another `Repro` transform name.

## Apply Transforms to Images

Moving image into fixed domain:

```python
warped_moving = ants.apply_transforms(
    fixed=fixed,
    moving=moving,
    transformlist=tx["fwdtransforms"],
    interpolator="linear",
)
```

Label image into fixed domain:

```python
warped_labels = ants.apply_transforms(
    fixed=fixed,
    moving=moving_labels,
    transformlist=tx["fwdtransforms"],
    interpolator="genericLabel",
)
```

Time series into a 3D reference:

```python
warped_timeseries = ants.apply_transforms(
    fixed=reference_3d,
    moving=timeseries_4d,
    transformlist=tx["fwdtransforms"],
    imagetype=3,
)
```

For masks, use `nearestNeighbor` and validate or re-threshold the result.

## Apply Transforms to Points

Point transforms require physical coordinates. A pandas DataFrame must have coordinate columns named `x`, `y`, and optionally `z` and `t`.

```python
import pandas as pd

moving_points = pd.DataFrame({"x": [14.0, 20.0], "y": [17.0, 25.0]})

def affine_inverse_flags(transformlist):
    return [str(item).endswith(".mat") for item in transformlist]

fixed_points = ants.apply_transforms_to_points(
    dim=2,
    points=moving_points,
    transformlist=tx["invtransforms"],
    whichtoinvert=affine_inverse_flags(tx["invtransforms"]),
)
```

Validate on one landmark with known direction before applying the transform to a full table. If your points are voxel indices, convert them to physical coordinates first with `ants.transform_index_to_physical_point`.

## Manual Transform Object IO

Create, save, reload, and apply a small affine transform:

```python
transform = ants.create_ants_transform(
    transform_type="AffineTransform",
    dimension=2,
    translation=(1.0, -2.0),
)
ants.write_transform(transform, "shift.mat")
loaded = ants.read_transform("shift.mat")
point_after = loaded.apply_to_point((10.0, 10.0))
```

Use `ants.create_ants_transform(supported_types=True)` to query installed transform-object names. Use `precision="float"` or `precision="double"` only.

## Compose and Average Transforms

For in-memory `ANTsTransform` objects:

```python
combined = ants.compose_ants_transforms([transform_a, transform_b])
```

All transforms in `compose_ants_transforms` must have the same dimension and precision.

For affine transform files:

```python
avg = ants.average_affine_transform(["subject1.mat", "subject2.mat"])
ants.write_transform(avg, "average_affine.mat")
```

For backend composition while applying image transforms:

```python
composite_filename = ants.apply_transforms(
    fixed=fixed,
    moving=moving,
    transformlist=tx["fwdtransforms"],
    compose="composite_",
)
if composite_filename is None:
    raise RuntimeError("composite transform was not written")
```

If `compose` does not end with `.h5`, ANTsPy appends a composite displacement-field filename pattern to the supplied prefix. Use a task-owned writable location and keep the returned filename.

## Multi-Metric Registration

`multivariate_extras` adds extra metrics to the deformable stage. It is intended for `SyNOnly` and `antsRegistrationSyN*` transform styles. Every metric entry has five values: metric name, fixed image, moving image, weight, and sampling parameter.

```python
metrics = [
    ("MeanSquares", fixed_feature, moving_feature, 0.5, 0),
    ("CC", fixed, moving, 0.5, 2),
]

tx = ants.registration(
    fixed=fixed,
    moving=moving,
    type_of_transform="SyNOnly",
    initial_transform=affine["fwdtransforms"][0],
    reg_iterations=(30, 10, 0),
    multivariate_extras=metrics,
)
```

The feature images must already be in compatible physical domains and should represent matched features, not arbitrary arrays.

## Masks and Initializers

Metric masks:

```python
tx = ants.registration(
    fixed=fixed,
    moving=moving,
    type_of_transform="AffineFast",
    mask=fixed_mask,
    moving_mask=moving_mask,
    mask_all_stages=False,
)
```

Rules:

- `mask` is in fixed image space.
- `moving_mask` is in moving image space.
- `mask_all_stages=True` applies masks to early stages as well as the final stage.

Affine initialization:

```python
init_mat = ants.affine_initializer(fixed, moving)
tx = ants.registration(
    fixed=fixed,
    moving=moving,
    type_of_transform="SyNOnly",
    initial_transform=init_mat,
    reg_iterations=(40, 20, 0),
)
```

Set `initial_transform="Identity"` to prevent automatic center-of-mass initialization.

## Motion Correction

For a 4D time-series image:

```python
mc = ants.motion_correction(
    image=bold_4d,
    fixed=fixed_3d,
    type_of_transform="BOLDRigid",
    mask=mask_3d,
)
```

Expected return keys include `motion_corrected`, `motion_parameters`, and `FD` in current source behavior. Treat returned transform parameters as registration outputs and validate their shapes before downstream use.

For manual control, split a 4D image into frames, register each frame to a fixed frame with a rigid/affine transform, and merge the corrected frames. Use the built-in helper unless a task specifically needs custom per-frame registration.

## Label-Driven Registration

When corresponding label images should drive registration:

```python
tx = ants.label_image_registration(
    fixed_label_images=[fixed_labels],
    moving_label_images=[moving_labels],
    fixed_intensity_images=fixed,
    moving_intensity_images=moving,
    initial_transforms="affine",
    type_of_deformable_transform="antsRegistrationSyNQuick[so]",
)
```

Keep label preprocessing and label-quality checks in segmentation-labels. Use this sub-skill for the registration call, transform lists, and transform application semantics.

## Template Building

Template building runs registration repeatedly. Keep test runs small:

```python
template = ants.build_template(
    image_list=[img1, img2, img3],
    iterations=1,
    type_of_transform="AffineFast",
    aff_iterations=(20, 0, 0, 0),
    aff_shrink_factors=(1, 1, 1, 1),
    aff_smoothing_sigmas=(0, 0, 0, 0),
)
```

Use `weights` to change image contributions and `initial_template` to seed the template. If `output_dir` is omitted, ANTsPy creates and removes a temporary work directory. Pass `output_dir` only when intermediate transforms must be inspected.

## Displacement Fields, Jacobians, and Warped Grids

Nonlinear registration diagnostics:

```python
warp_file = tx["fwdtransforms"][0]
jac = ants.create_jacobian_determinant_image(fixed, warp_file, do_log=True)
grid = ants.create_warped_grid(
    moving,
    transform=tx["fwdtransforms"],
    fixed_reference_image=fixed,
)
```

Warp image diagnostics:

```python
warp_image = ants.image_read(warp_file)
gradient = ants.deformation_gradient(warp_image, py_based=True)
rotation = ants.deformation_gradient(warp_image, to_rotation=True, py_based=True)
inverse_rotation = ants.deformation_gradient(warp_image, to_inverse_rotation=True, py_based=True)
```

Only use these diagnostics when a deformation warp exists. Pure affine registrations do not produce local warp fields.

## Displacement-Field Arithmetic

Create and round-trip a displacement-field transform:

```python
field_transform = ants.transform_from_displacement_field(field_image)
field_again = ants.transform_to_displacement_field(field_transform, fixed)
```

Compose and invert fields:

```python
composed = ants.compose_displacement_fields(update_field, total_field)
zero_inverse = field_image * 0
inverse = ants.invert_displacement_field(field_image, zero_inverse)
```

Simulate or fit a field for controlled experiments:

```python
simulated = ants.simulate_displacement_field(
    fixed,
    field_type="bspline",
    number_of_random_points=20,
    sd_noise=1.0,
    mesh_size=1,
)

fit_field = ants.fit_bspline_displacement_field(
    displacement_origins=origins,
    displacements=deltas,
    origin=fixed.origin,
    spacing=fixed.spacing,
    size=fixed.shape,
    direction=fixed.direction,
    number_of_fitting_levels=2,
    mesh_size=1,
)
```

Use small `number_of_random_points`, low `sd_noise`, and low fitting levels for smoke tests.

## B-Spline and Thin-Plate Spline Scattered Data

Fit a B-spline curve from scattered data:

```python
curve = ants.fit_bspline_object_to_scattered_data(
    scattered_data=scattered_values,
    parametric_data=parametric_points,
    parametric_domain_origin=[0.0],
    parametric_domain_spacing=[1.0 / (len(parametric_points) - 1)],
    parametric_domain_size=[len(parametric_points)],
    number_of_fitting_levels=3,
    mesh_size=1,
)
```

Fit a thin-plate spline displacement field:

```python
tps_field = ants.fit_thin_plate_spline_displacement_field(
    displacement_origins=origins,
    displacements=deltas,
    origin=fixed.origin,
    spacing=fixed.spacing,
    size=fixed.shape,
    direction=fixed.direction,
)
```

Check that origin, spacing, size, direction, and point dimensionality all agree before fitting.

## Landmark-Derived Transforms

Linear landmark transform:

```python
xfrm = ants.fit_transform_to_paired_points(
    moving_points=moving_landmarks,
    fixed_points=fixed_landmarks,
    transform_type="affine",
)
registered_point = xfrm.apply_to_point(tuple(fixed_landmarks[0]))
```

Nonlinear landmark transform requires a domain image:

```python
xfrm = ants.fit_transform_to_paired_points(
    moving_points=moving_landmarks,
    fixed_points=fixed_landmarks,
    transform_type="bspline",
    domain_image=fixed,
    number_of_fitting_levels=3,
    mesh_size=1,
)
```

`transform_type="syn"` returns a dict with forward/inverse and middle-space transforms. `transform_type="tv"` or `"time-varying"` returns forward/inverse transforms plus a velocity field. Validate the returned structure before applying it.

## Time-Varying Point Sets and Velocity Fields

For three or more point sets:

```python
tv = ants.fit_time_varying_transform_to_point_sets(
    point_sets=[points_t0, points_t1, points_t2],
    domain_image=fixed,
    number_of_time_steps=3,
    number_of_compositions=2,
    number_of_integration_steps=10,
)
forward = tv["forward_transform"]
velocity = tv["velocity_field"]
```

Integrate a velocity field:

```python
field = ants.integrate_velocity_field(
    velocity,
    lower_integration_bound=0.0,
    upper_integration_bound=1.0,
    number_of_integration_steps=10,
)
```

Keep time-varying workflows bounded. They are advanced and can be expensive.

## FSL Linear Matrix Conversion

Convert a 4x4 FSL-style linear matrix to an ANTs transform:

```python
import numpy as np

fsl_matrix = np.eye(4)
antspy_transform = ants.fsl2antstransform(fsl_matrix, reference_3d, moving_3d)
```

Both reference and moving images must be 3D. Validate the converted transform on known points or a small image before using it in a larger chain.

## Native Verification Candidates

Useful native candidates for later verification are targeted transform-object tests and selected small registration tests. Prefer selected tests from transform IO/application and tiny registration cases; avoid running the full registration test file by default because it includes expensive SyN, template, motion, and deformation-gradient coverage.

## Two Difficult Synthetic Usability Cases

1. Wrong order/inversion debugging: create a tiny affine transform file, apply it to an image and a point table with intentionally wrong `whichtoinvert`, then require the agent to diagnose why image and point directions differ and fix both calls.
2. Fast deterministic registration selection: given two tiny shifted images, require a bounded `Translation` or `AffineFast` registration, verify dict keys and transform files, apply the transform to image and points, and reject default long SyN for the smoke task.
