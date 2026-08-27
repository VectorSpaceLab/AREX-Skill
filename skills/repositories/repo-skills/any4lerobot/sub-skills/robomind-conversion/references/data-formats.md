# RoboMIND data formats and validation

## Required directory hierarchy

Use this logical layout; names are case-sensitive:

```text
<source-root>/
├── benchmark1_0_release/
│   ├── h5_agilex_3rgb/<task>/success_episodes/{train,val}/<episode>/trajectory.hdf5
│   ├── h5_franka_1rgb/<task>/success_episodes/{train,val}/<episode>/trajectory.hdf5
│   └── ...
├── benchmark1_1_release/
│   └── h5_<embodiment>/...
├── benchmark1_2_release/
│   └── h5_<embodiment>/...
├── language_description_annotation_json/
│   ├── h5_agilex_3rgb.json
│   ├── h5_franka_1rgb.json
│   ├── h5_franka_3rgb.json
│   ├── h5_simulation_franka.json
│   ├── h5_tienkung_xsens.json
│   └── h5_ur_1rgb.json
└── RoboMIND_v1_2_instr.csv
```

The release may contain only a subset of the listed embodiment directories.
The conversion route supports exactly the three release names and eight
physical names catalogued in [embodiments](embodiments.md). Simulation folders
and labels may appear in the source, but the documented conversion skips them
because their storage format is not compatible with this path.

For each selected task, require both `success_episodes/train` and
`success_episodes/val` directories or explicitly record an absent split. Do
not treat arbitrary directories as successful episodes. Discover
`trajectory.hdf5` recursively below each split and retain the episode path in
all diagnostics.

## HDF5 keys

For a selected embodiment config, each episode file is expected to contain:

```text
observations/
├── rgb_images/<configured RGB camera key>
└── depth_images/<configured depth base key>   # only when depth is selected
puppet/<configured state key>
master/<configured action key>
```

Configured RGB keys are read as `observations/rgb_images/<key>`. A configured
key ending in `_depth` is read as
`observations/depth_images/<key-without-final-_depth>` when `--save-depth` is
selected. State arrays are read from `puppet/<state-key>` and action arrays
from `master/<action-key>`, then emitted as `observation.states.<key>` and
`actions.<key>`.

The loader derives episode length from the first state array. Safe preflight
must verify that every state, action, RGB stream, and selected depth stream has
the same frame count; the evidence loader does not comprehensively enforce
this before indexing. Reject non-finite or rank-incompatible numeric arrays.
Episodes with fewer than 50 decoded frames are skipped by the source behavior.

## Image decoding and shape rules

RGB values are treated as encoded byte arrays and decoded with OpenCV color
mode. If decoding returns no image, only these raw byte counts are recognized:

| Raw RGB byte count | Fallback shape |
|---:|---|
| 2,764,800 | `(720, 1280, 3)` |
| 921,600 | `(480, 640, 3)` |

Depth values are decoded with unchanged OpenCV mode. If decoding fails, only
these byte counts are recognized:

| Raw depth byte count | Fallback shape |
|---:|---|
| 921,600 | `(720, 1280)` then add singleton channel -> `(720,1280,1)` |
| 307,200 | `(480, 640)` then add singleton channel -> `(480,640,1)` |

These fallback sizes are evidence-specific and use `uint8` buffer arithmetic;
do not reinterpret an arbitrary encoded buffer or guess a 16-bit depth dtype.
A failed decode with an unrecognized size is a hard data error. Validate the
resulting HWC rank and declared config shape before adding a frame.

For the four BGR embodiments in [embodiments](embodiments.md), reverse the
last RGB channel after decode. Do not reverse depth. For all other supported
embodiments, preserve the decoded channel order. Record the decision in the
conversion manifest because a visually plausible but wrong color order is hard
to detect after video encoding.

The source behavior has a special top-camera retry that toggles the declared
top shape between 720x1280 and 480x640 and toggles the matching top-depth
shape. It is not a general image resize. A safe implementation should attempt
one declared shape and at most one explicitly logged alternative, and should
stop on a different camera mismatch or unrelated writer exception.

## Language annotations

`RoboMIND_v1_2_instr.csv` is interpreted as a table containing `task` and
`instruction` columns. Duplicate rows are dropped before constructing a
`task -> instruction` lookup. Every selected task must resolve to exactly one
meaningful instruction after that normalization. A missing task is not repaired
from a folder name.

The optional per-embodiment JSON file contains records with at least an `id`
and `response`. The workflow filters records whose id identifies the selected
output task and split, then derives an episode/action-config key from the id's
parent component. Confirm this mapping against the HDF5 episode directory for
the release. Do not use a neighboring response when the id is ambiguous.

When no matching JSON record exists, preserve the explicit fallback
`{"task_summary": null, "steps": null}` and mark the episode metadata as
incomplete. The CSV instruction and JSON response serve different purposes:
the CSV supplies the per-frame natural-language task; JSON supplies optional
structured action/task annotation.

## LeRobot feature and metadata contract

Feature names are namespaced as follows:

```text
observation.images.<camera>
observation.states.<state>
actions.<action>
```

Image config entries use `dtype: video` for RGB and `dtype: image` for depth,
with names `height,width,rgb` or `height,width,channel`. Numeric entries use
`dtype: float32`, a one-dimensional shape, and a `names.motors` list. The
complete widths and camera sets are in [embodiments](embodiments.md).

The intended metadata declares `codebase_version: v3.0`, `fps: 30`, and the
selected embodiment as `robot_type`. The custom writer adds `episode_index`,
`length`, `tasks`, flattened statistics, and `action_config` to episode
metadata, and writes train/validation split ranges. Inspect the generated
metadata rather than trusting a successful process exit.

Depth is omitted unless explicitly selected. If selected, verify that the
installed LeRobot stats validator accepts one-channel depth statistics (the
expected non-count statistic shape is `(1,1,1)` in the evidence behavior).
This is a compatibility gate, not permission to alter a global library without
review.

## Read-only structural validation

Before a conversion, produce a report containing:

- selected benchmark and embodiment names;
- discovered task and split directories;
- missing or extra annotation files;
- config-derived HDF5 keys and expected widths/shapes;
- per-stream frame counts and dtype/rank checks;
- image decode/fallback classification and BGR decision;
- episodes below the 50-frame minimum;
- dirty-task classifications;
- output paths that already exist and would be removed;
- planned executor, CPU reservation, memory bound, and log path.

This report can operate on directory names and metadata. Do not turn it into a
real conversion, video encoder invocation, Ray task, or large fixture write.
