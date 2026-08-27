# Controller Configs and Action Splits

This reference covers the public controller loaders, the on-disk controller JSON shape, and how robosuite builds action vectors for composite controllers.

## 1) Loading controller configs

### Composite controllers

Use `load_composite_controller_config` for robot-level controller configs:

```python
from robosuite.controllers import load_composite_controller_config

# Robot default preset
config = load_composite_controller_config(robot="Panda")

# Named preset
config = load_composite_controller_config(controller="BASIC")

# Custom JSON path
config = load_composite_controller_config(controller="/path/to/controller.json")
```

Resolution rules:

- `controller=None` + `robot=...` loads `controllers/config/robots/default_<robot>.json`.
- If the robot-specific file is missing, robosuite falls back to `controllers/config/default/composite/basic.json`.
- A named controller loads `controllers/config/default/composite/<name>.json`.
- A path ending in `.json` is read directly.
- `body_parts["arms"]` is flattened into `body_parts["right"]` / `body_parts["left"]` in memory.

### Part controllers

Use `load_part_controller_config` for single-part presets in `controllers/config/default/parts/`:

```python
from robosuite.controllers import load_part_controller_config

part_cfg = load_part_controller_config(default_controller="OSC_POSE")
custom_part_cfg = load_part_controller_config(custom_fpath="/path/to/part.json")
```

This helper is the legacy / direct loader for arm-style controller presets and is still used by some robot loaders for base, torso, head, and leg parts.

Legacy refactor note:

```python
from robosuite.controllers.composite.composite_controller_factory import refactor_composite_controller_config

composite_cfg = refactor_composite_controller_config(
    controller_config=part_cfg,
    robot_type="Sawyer",
    arms=["right"],
)
```

- `refactor_composite_controller_config(...)` can promote an old single-part arm config into the current composite format.
- When a robot has a built-in composite preset, the refactor path starts from that preset and overrides the arm entries.
- When there is no built-in preset, the refactor path synthesizes a `BASIC` composite config and inserts the arm configs there.

## 2) On-disk controller JSON shape

A composite controller JSON usually looks like this:

```json
{
  "type": "BASIC",
  "body_parts": {
    "arms": {
      "right": { "type": "OSC_POSE", "gripper": { "type": "GRIP" } },
      "left": { "type": "OSC_POSE", "gripper": { "type": "GRIP" } }
    },
    "torso": { "type": "JOINT_POSITION" },
    "head": { "type": "JOINT_POSITION" },
    "base": { "type": "JOINT_VELOCITY" },
    "legs": { "type": "JOINT_POSITION" }
  },
  "composite_controller_specific_configs": {
    "ref_name": ["..."],
    "actuation_part_names": ["right", "left"]
  }
}
```

Key points:

- `type` selects the composite controller class.
- `body_parts` is the part-controller map.
- `composite_controller_specific_configs` is only needed for whole-body controllers and custom extensions.
- Arm entries usually include a nested `gripper` sub-config.

## 3) Action vectors and split indexes

A robot action is typically a flat vector. The robot or composite controller splits it into named parts.

Useful calls:

```python
robot.print_action_info()
robot.print_action_info_dict()
vector = robot.create_action_vector({
    "right": np.zeros(6),
    "right_gripper": np.array([0.0]),
})
```

Inverse helper:

```python
action_dict = robot.composite_controller.create_action_dict_from_action_vector(vector)
```

What to remember:

- `action_split_indexes` is an ordered mapping from part name to `(start, end)` slices.
- Grippers use their own `dof` when present.
- `HybridMobileBase` appends one extra scalar `base_mode` term.
- `WholeBodyIK` builds its split order from `actuation_part_names` first, then the remaining parts.
- `create_action_vector` validates per-part lengths; mismatches usually mean a wrong controller config, wrong gripper type, or wrong part name.

## 4) Controller families

| Type | Typical control space | Notes |
| --- | --- | --- |
| `OSC_POSE` | 6D pose | Delta by default; can be position-only with `OSC_POSITION`. |
| `OSC_POSITION` | 3D position | Same family as OSC pose, without orientation. |
| `IK_POSE` | 6D pose | Legacy IK path; only supported on a few robots. |
| `JOINT_POSITION` | Joint positions | Delta by default; variable impedance adds more action dims. |
| `JOINT_VELOCITY` | Joint velocities | Used by base, torso, head, and some arm configs. |
| `JOINT_TORQUE` | Joint torques | Direct torque passthrough. |
| `GRIP` | Gripper command | Used by simple gripper controllers. |

Interpolation support is intentionally narrow: the built-in configs use `linear` or `null`, and `ramp_ratio` controls how aggressively the interpolated command is ramped.

## 5) Whole-body specifics

`WHOLE_BODY_IK` and related extensions rely on `composite_controller_specific_configs`.

Common keys:

- `ref_name`: end-effector site names used by the IK solver.
- `actuation_part_names`: the parts handled by the whole-body solver.
- `nullspace_joint_weights`: posture bias for IK nullspace behavior.
- `ik_pseudo_inverse_damping`, `ik_integration_dt`, `ik_max_dq`, `ik_max_dq_torso`: IK tuning.
- `ik_input_type`, `ik_input_rotation_repr`, `ik_input_ref_frame`: target interpretation.

If you are debugging whole-body action routing, print the split map with `scripts/print_action_info.py` and compare it to the JSON config.
