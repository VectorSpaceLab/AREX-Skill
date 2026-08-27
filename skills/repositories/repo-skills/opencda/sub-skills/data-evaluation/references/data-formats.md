# OpenCDA dump and trajectory formats

## Evidence and scope

This guide is distilled from the OpenCDA 0.1.3 source at the requested source
revision, especially `opencda/core/common/data_dumper.py`,
`opencda/scenario_testing/utils/yaml_utils.py`, and
`scripts/generate_prediction_yaml.py`. It describes the data contract, not a
CARLA replacement. A dumped frame is expected to be ordinary YAML that can be
loaded as a mapping with a `vehicles` mapping.

## Dump layout

`DataDumper` creates a vehicle directory below a timestamped dump directory.
A typical data root is organized as:

```text
<data-root>/
  <scenario-or-time>/
    <vehicle-id>/
      000060.yaml
      000060_camera0.png
      000062.yaml
      ...
```

The exact parent naming can be chosen by the caller. The bundled offline helper
preserves the relative parent and frame filename in its separate output root;
it does not copy images or point clouds and never needs a simulator connection.
Frame files are ordered by filename, so zero-padded frame names are strongly
recommended.

`DataDumper.run_step` ignores the first 60 simulation steps and dumps every
other step. With the documented fixed timestep of 0.05 seconds (20 simulation
frames/second), this produces a 10 Hz YAML stream after the initial warm-up.
Do not mistake the raw simulator tick rate for the YAML sampling rate.

## Frame-level keys

A normal frame contains the following top-level records:

| Key | Shape and meaning |
| --- | --- |
| `vehicles` | Mapping from CARLA vehicle id to a vehicle record. YAML may deserialize numeric keys as integers. |
| `predicted_ego_pos` | Six values: `x, y, z, roll, yaw, pitch` for the localization estimate. |
| `true_ego_pos` | Six values in the same order for the true ego transform (or RSU-provided true pose). |
| `ego_speed` | Floating-point ego speed, in the OpenCDA speed convention (km/h from `get_speed`). |
| `lidar_pose` | Six world-frame pose values in the same order. |
| `camera0`, `camera1`, ... | Camera pose under `cords`, intrinsic matrix under `intrinsic`, and lidar-to-camera matrix under `extrinsic`. |
| `RSU` | `true` for a roadside-unit dump; `false` when a behavior agent supplied a planned trajectory. |
| `plan_trajectory` | Present for a non-RSU behavior agent; each item is `[x, y, speed]`. |

The dumper asserts that each dumped perceived vehicle has a valid CARLA id
(not `-1`). If perception-active mode supplies synthetic objects without a
CARLA id, dumping is intentionally rejected rather than producing ambiguous
labels.

## Vehicle record

Each entry under `vehicles` is created with these fields:

```yaml
vehicles:
  123:
    bp_id: vehicle.model.identifier
    color: "..."
    location: [x, y, z]
    center: [x, y, z]
    angle: [roll, yaw, pitch]
    extent: [x, y, z]
    speed: 12.3
```

`location` is the actor transform location. `center` is the bounding-box
center offset in the actor frame, and `extent` is the half-size of that box.
`angle` is ordered roll, yaw, pitch. `speed` comes from OpenCDA's `get_speed`
and is km/h unless the source function is explicitly called with its meters
flag. Preserve these units when comparing or plotting records.

## Trajectory tuple semantics

The prediction generator represents a vehicle state as a seven-value tuple:

```text
(x + center_x, y + center_y, z + center_z,
 roll, yaw, pitch, speed)
```

The first three values are the stored actor location plus the stored bounding
box center offset. They are not the raw `location` values and are not a
quaternion. The next three values retain roll/yaw/pitch order, and the last
value is speed. Treat each tuple as an observation of the target vehicle at one
10 Hz frame, not as a delta, control command, or interpolated state.

The offline helper adds two lists to every current vehicle record:

- `observations`: preceding frames for the same vehicle, excluding the current
  frame, up to `past_seconds * 10` records (default: 1 second / 10 records).
- `predictions`: following frames for the same vehicle, excluding the current
  frame, up to `future_seconds * 10` records (default: 8 seconds / 80 records).

The current frame is excluded from both lists. At the beginning or end of a
stream the list is shorter; no padding, extrapolation, or time interpolation is
performed. If the vehicle id is absent in a later frame, extraction stops at
that first missing frame. This is important: a disappearing vehicle is not
silently shifted onto another id or filled with stale state.

## Safe augmentation contract

The bundled helper loads one complete YAML sequence per vehicle directory,
augments in memory, validates the records it touches, then writes corresponding
YAML files under the requested output root. It uses PyYAML's safe loader and
never imports OpenCDA, CARLA, SUMO, a detector, or a network client.

- `--input-root` is required.
- `--output-root` is required unless explicit `--in-place` is supplied.
- Output is a separate tree and input files are not modified by default.
- Existing output files require `--overwrite`.
- `--in-place` is the explicit opt-in for replacing input YAML files.
- Only YAML files are generated; source images and point clouds remain outside
  the output tree and are not edited.
- `--past-seconds` and `--future-seconds` control whole 10 Hz windows and must
  be non-negative integers.

For reproducibility, keep frame names and parent directories stable and record
the chosen horizon arguments alongside any downstream metric.
