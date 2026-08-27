# IK API reference

`InverseKinematicsCfg.create` accepts `robot`, optimizer/metrics/transition YAMLs,
optional `scene_model`, `collision_cache`, `self_collision_check`, `DeviceCfg`,
`num_seeds`, position/orientation tolerances, `use_cuda_graph`, `random_seed`,
`max_batch_size`, `multi_env`, and `max_goalset`. Verified defaults include 32
seeds, 0.005 position tolerance, 0.05 orientation tolerance, self-collision on,
CUDA graphs on, and batch/goalset sizes of one.

`InverseKinematics(config)` exposes `tool_frames`, `joint_names`,
`default_joint_state`, `compute_kinematics`, `solve_pose`, `solve_state`, and
`update_world`. `solve_pose(goal_tool_poses, current_state=None, seed_config=None,
return_seeds=1, run_optimizer=True)` returns `IKSolverResult`.

`Pose(position, quaternion)` uses `(B,3)` and `(B,4)` tensors; quaternions are
wxyz. `GoalToolPose.from_poses` takes a dictionary keyed by the exact tool-frame
name and can specify `ordered_tool_frames`, `num_goalset`.

Use `max_batch_size >= B` for batched goals. A result's success mask is the
source of truth; error tensors are useful for ranking partial solutions but are
not a validity guarantee. `update_world` updates the scene cache in place when
capacity was configured; otherwise construct a solver with a larger
`collision_cache` before adding many object types.
