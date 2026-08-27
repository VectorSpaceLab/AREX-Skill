# Retargeting troubleshooting

- **Criteria key mismatch:** keys must identify configured robot tool frames;
  inspect `retargeter.tool_frames` and use exact names.
- **Sequence shape error:** record time, environment, frame, position, and
  quaternion axes; normalize input to the `SequenceGoalToolPose` contract.
- **Jitter:** use MPC/local tracking, smaller `optimization_dt`, a warm start,
  and explicit velocity/acceleration regularization rather than post-hoc
  smoothing that violates collision/limits.
- **Locked joints move:** check lock-joint mapping and source joint order before
  changing optimizer weights.
- **High-DoF OOM/slow solve:** reduce `num_envs`, seeds, control points, and
  sequence prefix; select a free GPU and retain collision checks.
- **External playback/data failure:** validate a tiny local frame sequence first;
  do not conflate dataset/download or viewer issues with solver correctness.
