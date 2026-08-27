---
name: motion-planning
description: "Plans collision-aware c-space, pose, and grasp motions with
  cuRobo's composed IK, graph-planning, and trajectory-optimization APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Motion planning

Use this route for collision-free robot paths, pose/c-space/grasp planning,
batched planning, graph planner selection, or planner scene updates. Read
[workflows.md](references/workflows.md) for composition and
[api-reference.md](references/api-reference.md) for result handling.

## Core workflow

1. Build `MotionPlannerCfg.create` with a robot, IK/trajopt/graph/metrics YAMLs,
   scene model, collision cache, batch shape, and CUDA `DeviceCfg`.
2. Construct `MotionPlanner`, inspect its tool frames/joint names, and prepare
   a named start `JointState` plus a reachable pose, c-space, or grasp goal.
3. Call the matching `plan_pose`, `plan_cspace`, or `plan_grasp`; inspect success,
   validity, collision metrics, and the interpolated trajectory before sending
   any command.
4. For a workcell update, call `update_world`; use attachment-manager and
   link-collision toggles only with an explicit scene model.
5. Scale seeds, graph samples, horizon, and batch only after a tiny plan works.
   Keep CUDA graphs enabled in production and use
   [scripts/plan_smoke.py](scripts/plan_smoke.py) for a non-interactive check.

IK is an internal planning stage; use [ik](../ik/SKILL.md) for target solving
alone and [collision-scenes](../collision-scenes/SKILL.md) for obstacle schema.
