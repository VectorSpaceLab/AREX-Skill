# Reference-motion API

## Data contract

`myosuite.logger.reference_motion.ReferenceMotion(reference_data,
motion_extrapolation=False, random_generator=None)` accepts a mapping or a
`.npz`, `.pkl`, or `.pickle` file. The mapping must contain `time`; supported
fields are:

- `robot`: a 2-D array `(N, n_robot_joints)` or `None`.
- `robot_vel`: a matching velocity array, or `None` when velocity is not used.
- `object`: a 2-D array `(M, n_object_coordinates)` or `None`.
- `robot_init` and `object_init`: optional 1-D initial states. Missing values
  are inferred from the first frame, except random references use the mean of
  their low/high range. Object init in 6-D position+Euler form is converted to
  7-D position+quaternion when the object trajectory is 7-D.

The implementation validates rank and dimension agreement. Arrays should be
numeric and use monotonically increasing, time-compatible `time` values. The
class rounds times to four decimal places to avoid floating-point slot misses.

## Classification and methods

`ReferenceType.FIXED`, `RANDOM`, and `TRACK` are selected from the number of
frames: one frame is fixed, two frames are low/high random bounds, and more than
two frames are a tracked trajectory. The public methods are:

- `get_init() -> (robot_init, object_init)` returns the initial states.
- `get_reference(time) -> ReferenceStruct` returns robot, velocity, object,
  and init fields. Fixed values are constant; random values are sampled from
  bounds; track values use exact frames or linear interpolation.
- `find_timeslot_in_reference(time) -> (previous, next)` locates a tracked
  interval and caches forward progress.
- `reset()` resets the cached slot index to zero.

With `motion_extrapolation=False` (default), a time beyond the final tracked
frame raises an assertion. With it enabled, the final frame is held after the
trajectory ends. This is zero-order hold, not a velocity-based extrapolation.

## JAX counterpart

`myosuite.logger.reference_motion_jax.ReferenceMotion` mirrors the NumPy API for
MJX/JAX workflows, but requires the optional JAX dependency. Compare outputs
with `np.asarray(...)` and `np.testing.assert_allclose`; do not import the JAX
counterpart on a base-only installation and do not call CPU parity proof CUDA
coverage.
