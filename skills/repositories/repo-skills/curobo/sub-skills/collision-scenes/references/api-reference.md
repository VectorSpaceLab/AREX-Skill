# Scene and collision API

`Scene`/`SceneCfg` is a typed collection of optional lists: `sphere`, `cuboid`,
`capsule`, `cylinder`, `mesh`, `voxel`, and generic objects. Each primitive has
an explicit name, dimensions/radius or mesh reference, and pose. Pose
quaternions use wxyz.

Public collision wrappers expose robot/world collision configuration and
checking for custom pipelines; solver configs normally own the scene collision
checker. Use `scene_model` for a bundled YAML and `update_world(Scene(...))`
for a runtime update. `collision_cache` is a per-type capacity map, not an
unbounded allocator.

Self-collision uses the robot's sphere approximation. `SelfCollisionCostCfg`
can set `store_pair_distance=True` to retain per-pair signed distances, at a
cost in memory/writes. The ordinary reduction returns the largest penetration
across enabled pairs. Link-collision enable/disable and attachment operations
must be reflected in the same scene model used by the solver.
