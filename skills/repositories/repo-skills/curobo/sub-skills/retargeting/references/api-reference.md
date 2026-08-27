# Retargeting API

`MotionRetargeterCfg.create` requires `robot` and
`tool_pose_criteria: Dict[str, ToolPoseCriteria]`. Important controls are
`num_envs`, `use_mpc`, `self_collision_check`, `scene_model`,
`optimization_dt`, `num_seeds_global`, `num_seeds_local`, `num_control_points`,
`steps_per_target`, position/orientation tolerances, and global/local IK and
MPC iteration overrides.

`MotionRetargeter` exposes `solve_frame`, `solve_sequence`, `reset`,
`default_joint_state`, `joint_names`, `num_dof`, and `tool_frames`.
`GoalToolPose`/`SequenceGoalToolPose` represent one or many tool goals; exact
batch/frame ordering must match the criteria and robot tool frames.

`ToolPoseCriteria` uses axis-weight and convergence-tolerance fields rather than
generic position/rotation constructor keywords. Its public fields include
`terminal_pose_axes_weight_factor`, `non_terminal_pose_axes_weight_factor`,
`terminal_pose_convergence_tolerance`, `non_terminal_pose_convergence_tolerance`,
`project_distance_to_goal`, and `device_cfg`. Use six-axis weights/tolerances
for position plus orientation criteria and keep them on the solver device.

Use `use_mpc=False` for global IK-style sequence solving when targets are
independent or initialization is needed. Use `use_mpc=True` for local temporal
tracking when a previous state/warm start and smooth control are important.
