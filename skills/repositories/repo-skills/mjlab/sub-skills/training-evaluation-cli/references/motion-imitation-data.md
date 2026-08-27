# Motion imitation data

This page covers the CSV-to-NPZ preprocessing workflow used by tracking tasks
and the validation rules that keep motion data compatible with mjlab.

## Source format

The installed converter expects a numeric CSV with no header.
Each row must contain:

| Columns | Meaning |
|---|---|
| 1-3 | base position `x, y, z` |
| 4-7 | base quaternion `x, y, z, w` |
| 8+ | joint positions in the task's DOF order |

The source converter interprets the quaternion as `xyzw` in the CSV and converts
it to `wxyz` before simulation. The CSV should contain at least two frames for
interpolation, and the output sequence should be long enough to support velocity
estimation.

## Frame-rate conversion

The converter interpolates the motion from `input_fps` to `output_fps`.
A good working estimate for the output frame count is:

```text
ceil((input_frames - 1) * output_fps / input_fps)
```

The bundled validator checks whether the selected input range produces a valid
interpolated length and whether the frame count is large enough for velocity
computation.

## W&B registry flow

Motion imitation tasks use a W&B motions registry:

- the converter uploads a generated `motion.npz`
- tracking tasks can consume a local `motion.npz` or a registry artifact
- playback from W&B expects the motions artifact type and the inner file name
  `motion.npz`

Use the registry name when you want a remote artifact, and use a local motion
file when you want a fully offline playback command.

## Converter output

The installed converter produces an NPZ with the precomputed kinematics needed
by tracking tasks, including:

- `fps`
- `joint_pos`
- `joint_vel`
- `body_pos_w`
- `body_quat_w`
- `body_lin_vel_w`
- `body_ang_vel_w`

## Why the local converter matters

Use the mjlab converter for motion preprocessing. Converters from other stacks
can write body arrays in a different order, which breaks tracking targets even
if the files appear superficially similar.

## Bundled validator

`validate_motion_csv_schema.py` checks the input before conversion.
It is intentionally conservative and local-only.

Typical checks:

- file exists and contains numeric rows
- selected line range is valid
- column count matches `7 + expected_dofs`
- selected frame count is enough for interpolation
- estimated output frame count is enough for velocity estimation

## Helpful validation example

The built-in G1 tracking converter expects 29 DOF columns after the 7 base
columns:

Run from this sub-skill directory, or replace `scripts/...` with the resolved
bundled helper path:

```bash
uv run python scripts/validate_motion_csv_schema.py motion.csv \
  --expected-dofs 29 \
  --input-fps 30 \
  --output-fps 50 \
  --line-range 1:120
```

## Play-time usage

For tracking tasks, playback usually needs one of these inputs:

- `--motion-file /path/to/motion.npz`
- `--registry-name entity/project/motions/name`
- `--wandb-run-path entity/project/run_id` when the motion comes from a run

If the motion file is wrong, the usual failure is not subtle: the policy will
track the wrong bodies or the converter will fail fast before training starts.
