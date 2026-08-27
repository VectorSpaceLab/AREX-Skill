---
name: collision-scenes
description: "Defines cuRobo robot/world collision scenes, sphere-based
  self-collision policy, attachments, caches, and collision-aware solver
  configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Collision and scenes

Use this route for obstacle schemas, world/self-collision, sphere fitting,
attachment geometry, signed distances, collision caches, and runtime scene
updates. Read [api-reference.md](references/api-reference.md) and
[sphere-approximation.md](references/sphere-approximation.md).

## Core workflow

1. Represent obstacles with `Scene` and typed `Cuboid`, `Sphere`, `Capsule`,
   `Cylinder`, `Mesh`, or `VoxelGrid` objects. Give each a unique name and a
   7-value pose `[x,y,z,qw,qx,qy,qz]`.
2. Enable scene collision through the solver config (`scene_model`, cache,
   `self_collision_check`) and size `collision_cache` for all runtime object
   types/counts.
3. Use sphere-based self-collision with conservative padding and an evidence-
   backed `self_collision_ignore` map. The max penetration reduction is the
   safety metric; pair distances are for diagnosis/map generation.
4. Use `update_world` for additions/moves/removals that fit cache capacity. For
   attached objects, update attachment and link-collision state together.
5. Validate the entire trajectory, not only endpoints. Use the bounded
   [scripts/collision_smoke.py](scripts/collision_smoke.py) fixture for typed
   scene construction; keep collision costs and convergence metrics enabled in
   accepted IK/planning/MPC results.

Use [troubleshooting.md](references/troubleshooting.md) for invalid objects,
cache, sphere, and GPU memory failures.
