# Dataset Layout And Frame Contract

## Directory shape

The downloaded/generated training data is organized conceptually as:

```text
<dataset-root>/
  Scenario1/                 # downloaded archives may use s1/s3/... aliases
    Town03/
      <route-id-or-run>/
        rgb/
        depth/
        semantics/
        lidar/
        topdown/
        label_raw/
        measurements/
```

The top-level scenario directory may use the archive labels `s1`, `s3`, `s4`,
`s7`, `s8`, `s9`, `s10`, or lane-change labels such as `left`, `right`, `ll`,
`lr`, `rl`, `rr`; the logical meaning is the same. Each scenario contains town
directories, and each town contains route/run directories. Do not flatten the
levels: the training configuration walks scenario → town → route before the
data loader indexes frame files.

Expected towns are `Town01`–`Town07` and `Town10HD`. A route directory must
contain all seven modality directories. `measurements/` is created by the
privileged `AutoPilot`; the other six are created and filled by `DataAgent`.

## Modalities and names

| Directory | Frame file | Producer/meaning |
|---|---|---|
| `rgb/` | `%04d.png` | Three 320×160 RGB views stitched horizontally: left, front, right; the saved image is 960×160 before downstream preprocessing. |
| `depth/` | `%04d.png` | Three depth views stitched like RGB; source depth is encoded by CARLA and decoded by the loader. |
| `semantics/` | `%04d.png` | Three semantic-segmentation views stitched like RGB; traffic-light classes may be rewritten using depth. |
| `lidar/` | `%04d.npy` | Saved CARLA LiDAR payload; the loader expects a NumPy object whose point array is element 1 and uses XYZI values. |
| `topdown/` | `encoded_%04d.png` | Encoded local bird's-eye semantic/agent map. The prefix is intentionally `encoded_`, unlike other modalities. |
| `label_raw/` | `%04d.json` | JSON list of privileged vehicle boxes/attributes, including the ego box. Future frames provide labels. |
| `measurements/` | `%04d.json` | Ego state, controls, navigation command, hazards, future ego waypoints, and `ego_matrix`. |

A frame id is the four-digit stem, with `topdown/encoded_` removed. For every
route, the seven frame-id sets must agree. A file existing in only one modality
is not a usable training frame. The validator checks names and JSON shape but
does not decode PNGs or execute NumPy.

## Measurement and label minimums

A generated measurement object should include:

```text
x, y, theta, speed, target_speed,
x_command, y_command, command, waypoints,
steer, throttle, brake, junction,
vehicle_hazard, light_hazard, walker_hazard, stop_sign_hazard,
angle, ego_matrix
```

The hazard values are either booleans or short future boolean arrays. `waypoints`
is a list of future ego tuples. `ego_matrix` is a 4×4 transform matrix. The
validator checks the key set and matrix/list shape where possible; it does not
invent missing control labels.

Each `label_raw/%04d.json` file is expected to be a JSON list. Entries normally
carry `class`, `extent`, `position`, `yaw`, `num_points`, `distance`, `speed`,
`brake`, `id`, and `ego_matrix`. Empty lists are syntactically valid but may be
unhelpful for perception training. Do not use an empty placeholder as evidence
that object labels were collected.

## Frame-window requirements

The default configuration uses `seq_len=1` and `pred_len=4`. The loader ignores
the first two and last two frames and, for each training sample, needs current
input frames plus future label frames. With those defaults, a route needs at
least ten synchronized frame ids to yield one conservative sample window. A
shorter route can pass a basic layout check but must fail a training-window
check (`--require-windows` in the bundled validator).

The data agent saves at half the 20 Hz simulation rate by default (`save_freq`
is ten simulator steps), so adjacent saved frame ids are collection ticks, not
raw CARLA frame numbers. Missing an id is still a synchronization failure.

## Storage and acquisition boundary

The public acquisition script expands multiple archives and requires about
**210 GB**. This skill never downloads, unpacks, deletes archives, or contacts
the dataset host. Before any external acquisition, confirm disk headroom,
license terms, archive checksums/transfer integrity, and the intended scenario
subset. Prefer a small CARLA collection or a copied fixture for validation.
The seven modality directories and synchronized frames are the acceptance
contract; disk usage alone is not proof of completeness.

## Relationship to training

The model-training workflow consumes route directories under the scenario/town
levels and loads current images/LiDAR/BEV/measurements plus future
`label_raw` files. If a validator reports missing `topdown`, `measurements`, or
future labels, do not try to repair it by changing model flags. Either finish
collection for the route or exclude it deliberately and record the exclusion.
For model config/backbone semantics, hand off to `model-training`.
