# RoboCasa data formats

Use these schemas for read-only inspection and for a written conversion plan.
They are distilled contracts, not a promise that every RoboCasa release uses
identical keys. If a key or shape differs, stop and resolve the source version
rather than silently adapting it.

## Raw HDF5 layout

A typical file has this shape:

```text
<data file>
├── data/                         (group; attrs include env_args)
│   ├── demo_<id>/                (group)
│   │   ├── obs/                  (group)
│   │   │   ├── robot0_agentview_left_image      [T,H,W,3] uint8 RGB
│   │   │   ├── robot0_agentview_right_image     [T,H,W,3] uint8 RGB
│   │   │   ├── robot0_eye_in_hand_image         [T,H,W,3] uint8 RGB
│   │   │   ├── robot0_base_to_eef_pos           [T,3]
│   │   │   ├── robot0_base_to_eef_quat          [T,4]
│   │   │   └── robot0_gripper_qpos              [T,2]
│   │   ├── actions                                [T,12]
│   │   ├── actions_abs                            [T,12] (rerender/source optional)
│   │   └── attrs: ep_meta (JSON), model_file (rerender/reset)
│   └── attrs: env_args (JSON)
└── mask/                        (optional group for curated subsets)
    ├── 30_demos                 [N] IDs, often byte strings
    └── 100_demos                [N] IDs, often byte strings
```

The `data` group attributes are not incidental. `env_args` describes the
RoboCasa environment and is needed by the reference rerender flow; a subset
copy must preserve it. A demo's `model_file` and initial `states[0]` are also
needed to restore the simulator. Original files may not have all rerender-only
keys.

### Required conversion observations

| Source key | Expected role | Expected per-frame contract |
|---|---|---|
| `obs/robot0_agentview_right_image` | right fixed camera | HWC RGB image, exactly 256x256x3 |
| `obs/robot0_agentview_left_image` | left fixed camera | HWC RGB image, exactly 256x256x3 |
| `obs/robot0_eye_in_hand_image` | wrist camera | HWC RGB image, exactly 256x256x3 |
| `obs/robot0_base_to_eef_pos` | end-effector position | float-like `[T,3]` |
| `obs/robot0_base_to_eef_quat` | end-effector orientation | float-like `[T,4]`; preserve quaternion ordering from source |
| `obs/robot0_gripper_qpos` | gripper state | float-like `[T,2]` |
| `actions` | control action | float-like `[T,12]` |
| demo attr `ep_meta` | language/task metadata | JSON object containing `lang` |

The state is `concatenate(pos, quat, gripper_qpos, axis=1)`, giving
`[T,9]`. It is not the simulator's flattened environment state. The action
vector is copied as `[T,12]` and is not converted to absolute actions by the
default route.

## Language metadata

`ep_meta` is stored as an HDF5 attribute and is JSON text (some HDF5 readers
may return bytes). Parse it, require an object, and require a string-like
`lang` field. Use the exact language string as the per-frame `task` metadata.
Do not derive task text from a filename, demo ID, or simulator environment
name when `lang` is absent. If the dataset has multiple language fields, record
which one was selected and preserve the original metadata separately.

## Default LeRobot feature contract

The source-derived conversion declares:

| LeRobot key | dtype | shape | axis names / notes |
|---|---|---:|---|
| `observation.images.robot0_agentview_right` | `video` | `(256,256,3)` | `height,width,channel` |
| `observation.images.robot0_agentview_left` | `video` | `(256,256,3)` | `height,width,channel` |
| `observation.images.robot0_eye_in_hand` | `video` | `(256,256,3)` | `height,width,channel` |
| `observation.state` | `float32` | `(9,)` | `state`; pos + quat + gripper |
| `action` | `float32` | `(12,)` | `actions` |

Dataset metadata also sets `robot_type` to `PandaOmron` and `fps` to `20`.
Treat these as source defaults, not universal truth for a modified robot or a
newer RoboCasa recording. Validate that the input control rate and embodiment
really match before labeling a dataset this way.

Every frame submitted to the writer includes the three RGB arrays, the state,
the action, and `task=ep_meta['lang']`. The default feature declaration has no
slots for depth, segmentation, camera matrices, rewards, dones, absolute
actions, or simulator states.

## Rerender-only observation families

The reference rerender flow can add keys with shapes determined by the
simulator and camera configuration:

| Family | Examples | Meaning / caution |
|---|---|---|
| Depth | `robot0_*_depth`, `robot0_*_depthW` | Normalized renderer depth versus converted world-depth; units and axis direction must be recorded |
| Calibration | `robot0_*_intrinsics` `[3,3]`, `robot0_*_extrinsics` `[4,4]`, `robot0_*_extrinsicsR` `[4,4]` | Intrinsics are computed from field of view and image size; extrinsics use simulator pose plus an axis correction; `R` is camera-model-relative, not interchangeable with world pose |
| Segmentation | simulator camera segmentation output | Mode is explicit (`element` in the reference flow, or another supported mode); label IDs are simulator-specific |
| Playback | `actions_abs`, `dones`, `rewards`, `states` | Additional action and simulator timeline data; `states` is flattened environment state, not the 9-value policy state |

For each fixed camera at height and width 256, the intrinsic matrix uses
`f = 0.5 * height / tan(fovy * pi / 360)` and principal point
`(width/2, height/2)`, yielding a 3x3 matrix. The source camera helper builds a
4x4 pose from simulator position/rotation, then applies the correction
`diag(1,-1,-1,1)` to align camera axes with the viewing convention. Record
whether an extrinsic is world-relative or camera-model-relative and the image
vertical-flip convention before comparing calibration across datasets.

The rerender loop reverses the renderer image row order for camera image-like
arrays while leaving depth-world and matrices on their own conventions. This
is an implementation detail to verify against the chosen robosuite version,
not a license to flip arbitrary arrays. Never infer calibration correctness
from array shape alone.

## Missing modality decision table

| Observation state | Safe action |
|---|---|
| 256x256 RGB present; depth/segmentation not requested | Convert with default schema after structural validation |
| RGB is 128x128; user only needs RGB | Ask whether a 128x128 custom schema is acceptable; do not silently resize into a claimed 256x256 contract |
| RGB is 128x128; user requires 256x256 | Rerender in RoboCasa/robosuite with assets, or obtain a trusted 256x256 source |
| Depth/segmentation absent; user requests them | Rerender; image interpolation cannot create physically valid modalities |
| Calibration absent; user needs camera geometry | Rerender or obtain calibration from the exact simulator/camera setup; record convention and units |
| Rerender produced extra arrays | Preserve source HDF5 or deliberately extend the LeRobot feature schema; default conversion drops them |
| `ep_meta.lang` absent | Stop or obtain an approved task-text mapping; never invent language labels |
