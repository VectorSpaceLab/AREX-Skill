# Reference-motion troubleshooting

## Missing or unreadable data

**Symptom:** `AssertionError: Missing key (time) in reference`, a rank
assertion, or a `TypeError: Unknown reference type`.

**Recovery:** pass a mapping or a supported `.npz`, `.pkl`, or `.pickle` path.
Ensure `time` exists, robot/object data is rank 2, init data is rank 1, and init
width equals the corresponding trajectory width. Validate a tiny mapping with
the bundled smoke helper before using a large file.

**Symptom:** file loads but a model fails when consuming the resulting frame.

**Likely cause:** robot/object joint order, quaternion convention, or dimensions
do not match the task. Check the target environment's `qpos` layout and object
coordinate convention. Do not “fix” a mismatch by truncating arrays.

## Wrong reference type

One row means `FIXED`; two rows are interpreted as low/high `RANDOM` bounds;
more than two rows are `TRACK`. If a two-frame recording was intended as a
short trajectory, add the intended intermediate frames or use a fixed/track
representation explicitly. Random references sample each `get_reference` call,
so use a controlled generator for reproducible tests.

## Time and interpolation errors

**Symptom:** `Trying to access time ... beyond max reference duration`.

**Recovery:** query within the final timestamp, or construct with
`motion_extrapolation=True` when final-frame hold is scientifically appropriate.
With extrapolation enabled, values after the final frame equal the final stored
frame; this is not dynamic prediction.

**Symptom:** unexpected interpolation or slow/backward playback.

**Recovery:** times must be sorted and replay should be monotonic. Call
`reset()` before a new pass because the lookup cache assumes forward progress.
Times are rounded to four decimal places, so avoid timestamps that are only
numerically distinct below that precision.

## Initialization and object coordinates

**Symptom:** initial state differs from the first trajectory row.

**Cause:** explicit `robot_init`/`object_init` is allowed to differ from frame
zero. For random references, omitted init values are derived from bounds; for
fixed/track references, they come from the first row. Inspect `get_init()` and
do not assume frame zero without checking.

**Symptom:** 6-D object init is rejected or does not match a 7-D object motion.

**Recovery:** use position + Euler only when the loader can convert it to
position + quaternion; otherwise provide the expected 7-D quaternion layout
explicitly and verify convention/order against the environment.

## CLI and rendering boundaries

`examine_reference` uses Click flags such as `--env_name`, `--horizon`,
`--num_playback`, and `--render none`. Quote environment arguments and use a
bounded horizon/count. A window/display error is not a reference-data error;
route it to `simulation-rendering` and keep a headless validation path.

## Optional JAX

If importing `reference_motion_jax` fails, install the documented optional MJX
extra in a separate compatible environment or use the NumPy implementation.
CPU NumPy parity is useful evidence but does not prove JAX or CUDA execution.
