# IK troubleshooting

- **Tool frame key error:** inspect `ik.tool_frames`; use the exact name in the
  `GoalToolPose` dictionary.
- **All goals fail:** test a target near the default pose, check radians, wxyz
  quaternion normalization, joint limits, and the position/orientation
  tolerances before increasing seeds.
- **Batch shape error:** ensure `Pose` rows are `(B,3)/(B,4)`, set
  `max_batch_size >= B`, and keep `num_goalset` consistent with goalset data.
- **Collision update fails:** pre-size `collision_cache` for every object type;
  call `update_world` rather than mutating config internals.
- **Solution is near target but colliding:** enable self/world collision and
  inspect collision metrics; do not simply disable costs.
- **CUDA graph failure after resizing:** reset or reconstruct the solver after
  changing batch shape; use eager mode only to isolate the cause.
- **OOM:** choose a free GPU, lower seeds/batch, and avoid allocating all
  reachability queries at once.
