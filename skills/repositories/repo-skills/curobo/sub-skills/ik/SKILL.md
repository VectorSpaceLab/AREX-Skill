---
name: ik
description: "Solves single, batched, collision-aware, and differentiable
  inverse-kinematics goals with cuRobo's CUDA IKSolver API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inverse kinematics

Use this route for pose IK, reachability sweeps, multi-seed solving, collision-
free goals, or updating the world without rebuilding a solver. Read
[api-reference.md](references/api-reference.md) for signatures and
[workflows.md](references/workflows.md) for recipes.

## Core workflow

1. Validate CUDA and choose a robot/tool frame. Build an `InverseKinematicsCfg`
   with `create(robot=..., num_seeds=...)`; add `scene_model`,
   `self_collision_check`, `collision_cache`, and `max_batch_size` when needed.
2. Construct `Pose` tensors with `(B,3)` positions and `(B,4)` **wxyz**
   quaternions, then wrap them as `GoalToolPose.from_poses({tool: pose})`.
3. Call `ik.solve_pose(goal, current_state=..., seed_config=...)`. Inspect
   `result.success`, `result.js_solution`, position/orientation error, and
   convergence before accepting a state.
4. For batches, allocate exactly the configured maximum shape and use the
   success mask; one unreachable pose must not invalidate the whole batch.
5. Call `ik.update_world(Scene(...))` for runtime obstacle changes. Use the
   bounded [scripts/ik_smoke.py](scripts/ik_smoke.py) helper for a headless
   check; reserve Viser, differential, and reachability viewers for a deliberate
   UI process.

Read [troubleshooting.md](references/troubleshooting.md) for target reachability,
shape, quaternion, collision-cache, and CUDA graph failures. Continue to
[motion-planning](../motion-planning/SKILL.md) when IK is only the first stage of
a collision-free path.
