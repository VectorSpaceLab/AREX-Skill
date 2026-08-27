# LIBERO HDF5 and LeRobot formats

## Source file layout

A source directory contains task files directly beneath the directory root:

```text
<suite-or-source>/
├── <task>_demo.hdf5
└── _SCENE<number>_<task>_demo.hdf5
```

Only the direct `*.hdf5` glob is in scope for the route. The filename is the
source of the instruction metadata; `_` becomes a space after the optional
`_SCENE<number>_` prefix and before `_demo`. A malformed filename is not a
license to guess an instruction.

Each file has this hierarchy:

```text
/
└── data/
    ├── demo_0/
    │   ├── actions                 (T, 7)
    │   ├── states                  (optional for conversion; simulator state)
    │   └── obs/
    │       ├── agentview_rgb       (T, H, W, 3)
    │       ├── eye_in_hand_rgb     (T, H, W, 3)
    │       ├── ee_states           (T, 6)
    │       ├── joint_states        (T, 7)
    │       └── gripper_states      (T, 2)
    └── demo_1/ ...
```

The converter reads `data` members and uses the frame count of
`obs/agentview_rgb`. The `states` dataset is retained by regeneration and may
be useful for simulator replay, but the core converter does not emit it as a
feature. A robust preflight should still report whether it exists and its
shape, because it is needed if the user later requests regeneration.

Required per-demo keys and semantic widths:

| HDF5 path | Meaning | Required width |
|---|---|---:|
| `obs/agentview_rgb` | fixed/world-facing RGB camera | 3 channels |
| `obs/eye_in_hand_rgb` | wrist/hand RGB camera | 3 channels |
| `obs/ee_states` | XYZ plus axis-angle orientation | 6 |
| `obs/joint_states` | robot joint positions | 7 |
| `obs/gripper_states` | two gripper state values | 2 |
| `actions` | XYZ/orientation command plus gripper | 7 |

`ee_states` is represented as position `(x,y,z)` followed by three axis-angle
components. It must not be interpreted as a quaternion without an explicit
conversion. `joint_states` and `gripper_states` are preserved as separate
observation streams.

## Output feature contract

The route's canonical feature declarations are:

| LeRobot key | dtype | shape | axes/labels |
|---|---|---:|---|
| `observation.images.image` | video | `(256,256,3)` | height, width, rgb |
| `observation.images.wrist_image` | video | `(256,256,3)` | height, width, rgb |
| `observation.state` | float32 | `(8,)` | ee 6 + gripper 2 |
| `observation.states.ee_state` | float32 | `(6,)` | position + axis-angle |
| `observation.states.joint_state` | float32 | `(7,)` | joints 0 through 6 |
| `observation.states.gripper_state` | float32 | `(2,)` | two gripper values |
| `action` | float32 | `(7,)` | six pose values + gripper |

The standard video metadata is 256x256, 3 channels, RGB, 20 FPS, no audio, and
an AV1/yuv420p encoding in the source's documented v3-style metadata. Treat
codec support as an environment/writer compatibility check; do not promise
that every LeRobot version accepts AV1. The canonical robot type is `franka`.

## State construction and gripper convention

For frame `t`:

```text
observation.state[t] = [ee_states[t], gripper_states[t]]
```

For source action `a`:

```text
action[t] = [a[0], a[1], a[2], a[3], a[4], a[5], 1 - clip(a[6], 0, 1)]
```

The source comment describes the expected convention as `-1=open, 1=close`
becoming `0=close, 1=open`; however, the implemented `clip` means values
below 0 map to 1 and values above 1 map to 0 after inversion. Preserve this
exact behavior when matching existing outputs, and flag out-of-range source
actions rather than silently claiming they have the nominal `[-1,1]` meaning.
Do not invert gripper *state* values: inversion applies to the final action
component only.

## 128x128 versus 256x256

The canonical converter feature shape is `(256,256,3)`. Original LIBERO files
are commonly `(128,128,3)`. These are not interchangeable declarations:

- Do not merely edit metadata to say 256 when bytes are 128.
- Do not silently resize in a generic adapter; resizing changes image evidence
  and may hide camera-orientation issues.
- If 128x128 is acceptable to the downstream model, use an explicitly adapted
  feature schema and validate that every writer/consumer supports it. Record
  the deviation from the canonical route.
- If the canonical schema is required, use the separately approved regeneration
  boundary with `resolution=256` and external simulator/assets. No simulator
  execution is performed by this skill.

Regenerated observations are rotated 180 degrees in the reference workflow to
correct an observed upside-down orientation on its target platform. Apply that
operation only once, at the approved regeneration/data-preparation stage; do
not rotate already corrected HDF5 frames during core conversion.

## Synthetic validation fixture

A safe structural fixture can be tiny and in memory or in a temporary directory:
create `/data/demo_0` with `T=2`, RGB arrays `(2,256,256,3)`, ee `(2,6)`, joints
`(2,7)`, gripper `(2,2)`, and actions `(2,7)`. Assert that required paths,
leading lengths, widths, finite values, and the expected action inversion are
correct. This is a schema test only: it must not invoke a writer, video
encoder, Hub client, Ray, or simulator.
