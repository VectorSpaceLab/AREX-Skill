# Motion-planning API

`MotionPlannerCfg.create` composes robot, IK optimizer/transition, metrics,
trajectory optimizer/transition, graph planner/rollout/transition, optional
scene model and cache, collision/self-collision settings, tolerances, device,
seeds, batch/goalset sizes, and interpolation settings. Its defaults use LBFGS
IK/trajopt plus an exact graph planner and CUDA graphs.

`MotionPlanner` exposes `plan_pose`, `plan_cspace`, `plan_grasp`, `update_world`,
`compute_kinematics`, `warmup`, `enable_link_collision`,
`disable_link_collision`, `attachment_manager`, `joint_names`, and
`default_joint_state`. `BatchMotionPlanner` provides the corresponding
multi-environment route where the configured batch and goalset semantics are
explicit.

A planner result is not automatically executable. Check its success/validity,
trajectory, pose/c-space error, collision distances, and interpolation before
commanding. Use the planner's configured interpolation `dt`; do not assume the
optimizer knot spacing is the controller timestep.
