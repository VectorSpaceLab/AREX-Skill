# Planning troubleshooting

- **No path:** first solve the same goal with IK, then inspect joint limits,
  scene clearance, graph connectivity, seed count, and transition horizons.
- **Planner config mismatch:** keep IK, trajopt, graph, metrics, and transition
  YAMLs from compatible families; use the public factory rather than mixing v1
  names or arbitrary internal dictionaries.
- **Path is colliding:** validate every interpolated point, scene object pose,
  self-collision ignore map, and attached-object geometry. Never validate only
  the optimizer endpoints.
- **World update fails:** pre-size `collision_cache` for object types/counts and
  call `update_world`; reconstruct when the required capacity exceeds cache.
- **Batch/shape failure:** set max batch/goalset before construction and keep
  start/goal shapes explicit; reset/rebuild CUDA graphs after shape changes.
- **Slow or OOM:** reduce graph samples, seeds, horizon, or batch, select a free
  GPU, and use timing only after correctness is established.
