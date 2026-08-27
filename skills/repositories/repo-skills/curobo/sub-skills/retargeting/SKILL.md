---
name: retargeting
description: "Retargets frame and tool-pose sequences to cuRobo robot joint
  trajectories using global IK or local MPC with collision constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Motion retargeting

Use this route for humanoid/high-DoF retargeting, frame-by-frame tool goals,
sequence goals, joint locks, global IK, local MPC, and scene-aware retargeting.
Read [api-reference.md](references/api-reference.md) and
[retargeting-workflows.md](references/retargeting-workflows.md).

## Core workflow

1. Choose a validated robot config and define a `ToolPoseCriteria` dictionary
   for each tool/frame to track. Verify frame names, weights, tolerances, and
   position/orientation conventions.
2. Build `MotionRetargeterCfg.create(robot=..., tool_pose_criteria=...)` with
   `num_envs`, `use_mpc`, seed counts, `steps_per_target`, timing, collision,
   and optional scene settings.
3. Feed one frame to `solve_frame` or a correctly shaped sequence to
   `solve_sequence`; inspect success, joint limits, collision metrics, and
   temporal smoothness before commanding.
4. Lock joints only when the mechanical/task constraint is explicit. For
   high-DoF robots, start with a short sequence and a small environment count,
   then scale GPU memory and control points.
5. Keep external SOMA/input datasets and interactive playback separate from
   the reusable solver path. Use the bounded
   [scripts/retarget_config_smoke.py](scripts/retarget_config_smoke.py) helper
   for criteria parsing and [troubleshooting.md](references/troubleshooting.md)
   when shapes or criteria fail.

For the underlying IK/MPC contracts, read [ik](../ik/SKILL.md) and
[mpc-optimization](../mpc-optimization/SKILL.md).
