# RoboTwin/XPolicyLab adapter contract

RoboTwin's evaluation adapter translates RoboTwin observations and policy actions into XPolicyLab conventions.

## Observation sent to policy

The adapter builds a dict like:

```python
{
  "data_format_version": "v1.0",
  "instruction": "...",
  "instructions": ["..."],
  "env_idx": 0,
  "vision": {...},
  "state": {...},
  "additional_info": {"frequency": 30},
}
```

## Vision mapping

| RoboTwin observation key | XPolicyLab key |
| --- | --- |
| `observation/head_camera` | `vision/cam_head` |
| `observation/left_camera` | `vision/cam_left_wrist` |
| `observation/right_camera` | `vision/cam_right_wrist` |
| `third_view_rgb` | `vision/cam_third_view` |

Each camera can include `color`, `depth`, `intrinsic_matrix`, `extrinsics_matrix`, and `shape` when present in the source observation.

## State mapping

| RoboTwin key | XPolicyLab state key |
| --- | --- |
| `joint_action/left_arm` | `left_arm_joint_state` |
| `joint_action/left_gripper` | `left_ee_joint_state` |
| `joint_action/right_arm` | `right_arm_joint_state` |
| `joint_action/right_gripper` | `right_ee_joint_state` |
| `endpose/left_endpose` | `left_ee_pose` |
| `endpose/right_endpose` | `right_ee_pose` |
| robot TCP helpers when available | `left_tcp_pose`, `right_tcp_pose` |

## Policy action responses

The adapter accepts:

- A mapping representing one action.
- A mapping with an `actions` key containing a chunk.
- A NumPy array or sequence of arrays/mappings.

Empty chunks are errors.

## Action types

`joint` and `qpos` normalize to RoboTwin `qpos`. `ee` and `endpose` normalize to RoboTwin `ee`.

For `qpos`, action mappings may contain:

- Left arm: `left_arm_joint_state`, `left_arm_joint`, `left_joint_state`, `arm_joint_state`, or `joint_state`.
- Right arm: `right_arm_joint_state`, `right_arm_joint`, or `right_joint_state`.
- Left gripper: `left_ee_joint_state`, `left_gripper`, `left_gripper_pos`, or `ee_joint_state`.
- Right gripper: `right_ee_joint_state`, `right_gripper`, or `right_gripper_pos`.

For `ee`, arm pose arrays must be 7D and may use `left_ee_pose`, `left_endpose`, `ee_pose`, `right_ee_pose`, or `right_endpose`.

When a field is missing, the adapter falls back to the current observation if possible. Missing fields without fallback raise a `KeyError`; wrong 7D pose shape raises `ValueError`.

## Flat action order

The final flat action passed to RoboTwin is:

```text
left_arm..., left_gripper, right_arm..., right_gripper
```

Use bundled `check_action_adapter.py` to validate qpos and endpose mappings synthetically before launching a policy rollout.
