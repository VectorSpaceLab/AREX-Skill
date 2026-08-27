# AgiBotWorld data formats

Use this document for a read-only schema check before conversion. It describes
what the route consumes and emits; it is not a promise that arbitrary AgiBot
releases have every optional modality.

## Raw-tree contract

```text
release-root/
├── task_info/
│   ├── task_327.json
│   └── task_475.json
├── observations/
│   ├── 327/<episode-id>/
│   │   ├── videos/
│   │   │   ├── head_color.mp4
│   │   │   ├── head_center_fisheye_color.mp4
│   │   │   └── ...
│   │   ├── tactile/                 # tactile route only
│   │   │   ├── left_sensor_1.mp4
│   │   │   └── ...
│   │   └── depth/
│   │       ├── head_depth_000000.png
│   │       └── ...
│   └── 475/<episode-id>/...
└── proprio_stats/
    ├── 327/<episode-id>/proprio_stats.h5
    └── 475/<episode-id>/proprio_stats.h5
```

The converter discovers JSON files under `task_info/`, derives the numeric task
ID from the filename, and uses task metadata episode IDs for scheduling. The
observation and proprioception episode directories must use that numeric ID.
A directory found by scanning observations is only a fallback when a task
record has no episode list; it does not make missing task metadata valid.

Each task JSON is a list of episode records. The route requires, at minimum:

```json
{
  "episode_id": 0,
  "task_name": "place the object",
  "init_scene_text": "a block is on the table",
  "label_info": {
    "action_config": ["dataset-specific action labels"]
  }
}
```

The exact contents of `action_config` are preserved as episode metadata. The
frame-level task string is `task_name | init_scene_text`; it is repeated on
all frames in that episode so that task indices can be reconstructed by the
LeRobot writer.

## Proprioception HDF5 contract

Every episode has `proprio_stats.h5` with nested state and action datasets.
Configuration keys such as `joint.position` map to HDF5 paths by replacing dots
with slashes:

```text
state/joint/position
state/end/position
state/effector/position
action/joint/position
action/end/position
action/effector/position
```

The emitted LeRobot keys add semantic prefixes:

| Raw group | LeRobot frame key | Meaning |
|---|---|---|
| `state/<name>` | `observation.states.<name>` | state at the current frame |
| `action/<name>` | `actions.<name>` | action aligned to the current frame |
| task JSON instruction | `task` during writing | natural-language task label |

The selected end-effector schema determines which keys are read. A missing
configured HDF5 dataset is a schema error; do not silently substitute a
similarly shaped field from another group.

### Feature families

The shared base schema includes these state families:

- `effector.position`: two values for gripper/tactile configurations, or
  twelve joint values for dexhand.
- `end.orientation`: two quaternions (shape 2x4).
- `end.position`: two XYZ vectors (shape 2x3).
- `head.position`: yaw and pitch (shape 2).
- `joint.current_value` and `joint.position`: 14 arm-joint values.
- `robot.orientation`: one quaternion (shape 4).
- `robot.position`: one XYZ vector (shape 3).
- `waist.position`: pitch and lift (shape 2).

The action family includes `effector.position`, `end.orientation`,
`end.position`, `head.position`, `joint.position`, `robot.velocity`, and
`waist.position`. Shapes and motor names come from the selected configuration;
use the actual emitted `meta/info.json` as the acceptance authority rather
than assuming all listed fields occur in every release.

### End-effector differences

- **gripper** uses two-value `effector.position` with left/right gripper names,
  the base state/action groups, and the standard camera set.
- **dexhand** replaces `effector.position` with twelve hand-joint values for
  both state and action while retaining the other base groups. Its configured
  hand cameras are fisheye streams.
- **tactile** uses the gripper numeric schema and adds four sensor video keys:
  `left_sensor_1`, `left_sensor_2`, `right_sensor_1`, and `right_sensor_2`.
  Sensor videos are stored under `tactile/`, not under `videos/`.

All numeric features are declared float32. Preserve multidimensional arrays as
multidimensional features; flattening a quaternion or end-effector matrix can
make downstream motor names and statistics incorrect.

## Image and video features

Configured camera names become `observation.images.<name>` keys. The standard
RGB/depth declarations include:

| Feature suffix | Declared type | Declared shape | Source |
|---|---|---:|---|
| `head` | video | 480x640x3 | `videos/head_color.mp4` |
| `head_center_fisheye` | video | 768x960x3 | `videos/head_center_fisheye_color.mp4` |
| `head_left_fisheye` | video | 768x960x3 | matching `*_color.mp4` |
| `head_right_fisheye` | video | 768x960x3 | matching `*_color.mp4` |
| `hand_left`, `hand_right` | video | 480x640x3 | matching `*_color.mp4` in gripper schema |
| `hand_left_fisheye`, `hand_right_fisheye` | video | 768x960x3 | matching `*_color.mp4` in dexhand schema |
| `back_left_fisheye`, `back_right_fisheye` | video | 768x960x3 | matching `*_color.mp4` |
| `head_depth` | image | 480x640x1 | depth files, only with `--save-depth` |
| tactile sensor keys | video | 700x400x3 | `tactile/<sensor-key>.mp4` |

Video paths are passed to the custom writer separately from numeric frame
records. The writer adds timestamps and frame indices, computes task indices,
and records video references in episode metadata. Missing video files should
be classified before conversion; a corrupt existing MP4 is a skipped episode,
not an excuse to emit a video feature with a fabricated path.

Depth PNG/array values are converted to float32 and divided by 1000, so a raw
value of 1000 represents one metre. The number of depth images must equal the
number of state frames. A current LeRobot stats validator may reject depth
statistics under a color-only image rule. The repository README calls out this
specific depth-aware stats assertion as a compatibility point; use a reviewed
LeRobot-compatible depth-aware stats path or stop, rather than disabling
validation and publishing uncertain statistics.

## Alignment and short episodes

Let `N` be the length of the first non-empty state stream. The route expects all
state streams to provide `N` samples. For each action key:

1. length `N`: use it directly;
2. length `0`: emit a zero vector of that feature's configured shape for every
   frame;
3. length below `N`: load the corresponding state-shaped array and replace its
   recorded action indices with the available action values; if an end-index
   array is empty, the route may use the corresponding joint index;
4. length above `N`: classify the episode as corrupt and skip it.

This reconstruction preserves alignment only when the index array and feature
shape are valid. If an index is out of bounds, has duplicates that change
meaning, or does not match the action width, stop for review. A short-action
case should be tested with a synthetic HDF5 fixture containing both valid and
invalid indices.

The number of frames written is `N`. Task labels are added to every frame;
`action_config` is attached once at episode save time. Dirty tasks documented by
the dataset include episodes with action length greater than state length and
corrupted MP4s; those episodes are intentionally skipped.

## Output contract

The final LeRobot metadata should preserve:

- `codebase_version` for the installed target format (the repository example
  targets v3.0, but the installed LeRobot version is authoritative);
- robot type `a2d`, FPS 30, and the selected end-effector feature schema;
- `observation.images.*`, `observation.states.*`, and `actions.*` features with
  declared dtype, shape, and names;
- task labels and task indices for each frame;
- per-episode length, statistics, video paths/metadata, and `action_config`.

Inspect the output metadata and representative samples after conversion. Do
not assume that a custom writer designed for one LeRobot release is portable to
another without an import and signature check.
