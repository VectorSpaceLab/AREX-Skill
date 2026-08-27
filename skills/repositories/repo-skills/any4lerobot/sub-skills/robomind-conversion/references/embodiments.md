# RoboMIND embodiment and feature catalog

The configuration mapping uses the physical names below. Feature names are
formed by prefixing image, state, and action keys with
`observation.images.`, `observation.states.`, and `actions.` respectively.
Shapes are HWC for images and one-dimensional widths for numeric features.

| Embodiment | RGB cameras / shape | Depth cameras / shape | State keys (width) | Action keys (width) |
|---|---|---|---|---|
| `agilex_3rgb` | `camera_front`, `camera_left_wrist`, `camera_right_wrist` / 480x640x3 | same three camera bases / 480x640x1 | `end_effector_left`, `end_effector_right`, `joint_effort_left`, `joint_effort_right`, `joint_position_left`, `joint_position_right`, `joint_velocity_left`, `joint_velocity_right` / 7 each | same eight keys / 7 each |
| `franka_1rgb` | `camera_top` / 720x1280x3 | `camera_top` / 480x640x1 | `end_effector` / 6; `joint_position` / 8 | `joint_position` / 8 |
| `franka_3rgb` | `camera_top` / 720x1280x3; `camera_left`, `camera_right` / 480x640x3 | top / 720x1280x1; left/right / 480x640x1 | `end_effector` / 6; `joint_position` / 8 | `joint_position` / 8 |
| `franka_fr3_dual` | `camera_front`, `camera_top` / 720x1280x3; `camera_left`, `camera_right` / 480x640x3 | front/top / 720x1280x1; left/right / 480x640x1 | `end_effector` / 12; `joint_position` / 16 | `joint_position` / 16 |
| `tienkung_gello_1rgb` | `camera_top` / 480x640x3 | `camera_top` / 480x640x1 | `joint_position` / 16 | `joint_position` / 16 |
| `tienkung_prod1_gello_1rgb` | `camera_top` / 720x1280x3 | `camera_top` / 720x1280x1 | `joint_position` / 16 | `joint_position` / 16 |
| `tienkung_xsens_1rgb` | `camera_top` / 480x640x3 | `camera_top` / 480x640x1 | `end_effector` / 12; `joint_position` / 14 | `end_effector` / 12; `joint_position` / 14 |
| `ur_1rgb` | `camera_top` / 480x640x3 | `camera_top` / 480x640x1 | `end_effector` / 6; `joint_position` / 7 | `joint_position` / 7 |

## Numeric name details

Single-arm Franka and UR joint vectors use seven joints plus gripper where the
config declares width 8 for Franka and width 7 for UR. Dual Franka uses left
and right seven-joint-plus-gripper segments (16 total) and an end-effector
vector of 12 values. AgileX has left/right 7-wide streams for each of its
end-effector, effort, position, and velocity groups. TienKung Gello vectors
contain left/right arm components plus hand closure entries. TienKung Xsens
uses two 7-wide arm segments and separate 12-wide finger/end-effector values.

Preserve the configured motor name lists, including unusual spaces in the
TienKung hand-closure names, when creating metadata. Do not rename a key to
make it look cleaner: downstream consumers may depend on the original names.
For `franka_fr3_dual`, the end-effector names are grouped as left/right
XYZ-RPY values; the declared shape is authoritative even though names are
compact.

## Color and depth policy

Apply BGR-to-RGB conversion to all decoded RGB cameras for:

- `franka_1rgb`
- `franka_3rgb`
- `franka_fr3_dual`
- `ur_1rgb`

The conversion is a reversal of the final channel (`[..., ::-1]`) after OpenCV
color decode. Never apply it to depth. For `agilex_3rgb` and all TienKung
embodiments, keep the decoded RGB order as supplied by the workflow contract.
If provenance does not establish channel order for a new release, stop for a
choice rather than inferring it from the embodiment name.

## Shape fallback policy

The evidence configs declare a mix of 720x1280 and 480x640 streams. If the
Franka/UR top-camera stream arrives in the alternate known raw shape, an
explicit compatibility plan may switch the top camera to the alternate shape
and switch its top-depth declaration in lockstep. This is a shape declaration
fallback, not interpolation. The fallback does not rewrite the left/right
camera declarations in multi-camera Franka configurations.

Use one bounded fallback attempt per task. Record the initial shape, observed
raw byte count or decoded shape, fallback shape, and affected cameras. A
malformed payload whose size matches neither known fallback, or a mismatch in
an unaffected camera, remains an error.

## Unsupported registry labels

The registry may contain `sim_franka_3rgb` and `sim_tienkung_1rgb` placeholders,
and the source documentation mentions simulation variants. They do not carry a
usable physical feature config for this route and are not among the supported
CLI embodiment choices. Reject them rather than passing an empty config into a
writer. Simulation conversion is outside this sub-skill.

## Config-to-file mapping

For every config entry, derive source paths mechanically:

```text
image key camera_x       -> observations/rgb_images/camera_x
image key camera_x_depth -> observations/depth_images/camera_x   # save-depth only
state key state_name     -> puppet/state_name
action key action_name   -> master/action_name
```

Validate the paths before any frame is materialized. The config is the schema;
folder names alone do not justify adding a missing camera or numeric field.
