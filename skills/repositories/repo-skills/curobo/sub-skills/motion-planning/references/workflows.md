# Planning workflows

## Pose planning

Start with `franka.yml` or another validated robot config, a simple target
`Pose`, and a small scene. `plan_pose` uses the tool frame and composes IK,
graph search, and trajectory optimization. Verify FK at the final state and
check the complete interpolated trajectory for collision.

## C-space and grasp planning

Use `plan_cspace` when the desired joint configuration is authoritative. Use
`plan_grasp` when the goal includes grasp/tool pose and approach semantics;
record tool-frame and grasp-frame names. For attached objects, configure the
attachment manager and update collision geometry consistently.

## Graph planner choices

Exact graph planning is a good bounded baseline. PRM/transition graph variants
are useful when the workcell has difficult free-space connectivity, but require
consistent graph planner, rollout, and transition YAMLs. Treat graph failures
as connectivity/configuration evidence rather than immediately increasing
optimizer iterations.

## Batch planning

Set `max_batch_size` and goalset dimensions before construction. Use success
masks and per-goal metrics; do not broadcast a single start state accidentally
across robot environments.
