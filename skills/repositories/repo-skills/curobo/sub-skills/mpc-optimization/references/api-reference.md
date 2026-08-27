# Optimization API

`TrajectoryOptimizerCfg.create` defaults to LBFGS B-spline trajectory config,
four seeds, 5 mm/0.05 pose tolerances, CUDA graphs, 2 ms–200 ms trajectory dt
bounds, and interpolation `dt=0.025`. `TrajectoryOptimizer`/`TrajOptSolver`
exposes `solve_pose`, `solve_cspace`, `solve_state`, `get_interpolated_trajectory`,
`compute_trajectory_dt`, and goal/cost toggles.

`ModelPredictiveControlCfg.create` defaults to LBFGS MPC, `optimization_dt=0.02`,
four interpolation steps, warm-start iterations 200, cold-start iterations
300, safe deceleration on failure, and CUDA graphs. `MPCSolver` exposes
`update_current_state`, `update_goal_state`, `update_goal_tool_poses`,
`warm_start_solve`, `cold_start_solve`, `optimize_next_action`,
`optimize_action_sequence`, and `prepare_safe_deceleration_trajectory`.

The lower-level rollout graph composes `RobotStateTransition`, cost managers,
scene collision, metrics, and sampled action seeds. Toggle cost components by
name only when the config registers them; preserve collision and convergence
metrics when interpreting a result.
