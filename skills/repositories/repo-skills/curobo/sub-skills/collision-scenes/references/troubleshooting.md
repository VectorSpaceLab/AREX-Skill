# Collision troubleshooting

- **Object schema error:** use the matching typed obstacle, unique names, valid
  dimensions, and a wxyz 7-value pose. Keep mesh/voxel paths accessible to the
  runtime user.
- **New object rejected:** enlarge the per-type `collision_cache` and rebuild
  if capacity was exceeded; do not mutate private buffers.
- **False self-collision:** inspect sphere padding, link-pair ignore map, joint
  limits, and pair distances with `store_pair_distance=True`.
- **Missed collision:** increase sphere density or conservative padding and
  validate against mesh geometry before changing solver tolerances.
- **Trajectory endpoint passes but path collides:** run collision checks at the
  planner's interpolated samples and include attached-object geometry.
- **OOM/slow kernel:** select a free GPU, lower batch/seed count and sphere
  density, and avoid storing every pair distance in normal runtime.
