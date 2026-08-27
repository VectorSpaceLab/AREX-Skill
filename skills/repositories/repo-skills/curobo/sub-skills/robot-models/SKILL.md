---
name: robot-models
description: "Build cuRobo robot models from YAML or URDF, inspect joint and
  tool-frame contracts, and run CUDA forward kinematics with differentiable
  batched tensors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Robot models and kinematics

Use this route for URDF/YAML loading, robot builder decisions, joint-name or
link-frame debugging, FK/Jacobian queries, robot spheres, and pose/state tensor
construction. Read [api-reference.md](references/api-reference.md) for verified
signatures and [robot-builder.md](references/robot-builder.md) for URDF and
sphere-approximation workflow choices.

## Core workflow

1. Select a bundled robot config and its tool frame; verify URDF, joint names,
   limits, collision spheres, and `tool_frames` are coherent.
2. Build `KinematicsCfg` with `from_robot_yaml_file(...)`, supplying a
   `DeviceCfg` when the default CUDA device is not appropriate. Construct
   `Kinematics` only after a CUDA tensor probe succeeds.
3. Create `(B, dof)` float32 positions with `JointState.from_position(q,
   joint_names=kin.joint_names)`. Call `compute_kinematics` and inspect
   `tool_poses`, link poses, and Jacobians in the returned `KinematicsState`.
4. For reachability or optimization, pass a batch of configurations; retain
   `requires_grad=True` when differentiating a scalar loss through FK.
5. Use [scripts/fk_smoke.py](scripts/fk_smoke.py) for a bounded CUDA sanity
   check; it intentionally avoids benchmark timing and interactive visualization.

Use [troubleshooting.md](references/troubleshooting.md) when a YAML, URDF,
frame, device, quaternion, or shape error appears. Collision-aware consumers
continue in [collision-scenes](../collision-scenes/SKILL.md), and target solving
continues in [ik](../ik/SKILL.md).
