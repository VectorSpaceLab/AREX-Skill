---
name: modeling-simulation
description: "Build, step, and debug core Newton simulation models, states,
  controls, contacts, worlds, shapes, joints, and public loop patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Newton modeling and simulation

Use this sub-skill when the task is to create or debug a Newton model, state, control, shape, joint, articulation, world replication, collision-pipeline allocation, or a minimal simulation loop with public APIs.

## Route here for

- `newton.ModelBuilder`, `newton.Model`, `newton.State`, `newton.Control`, and `newton.Contacts` usage.
- Choosing `add_body()` versus `add_link()` and connecting links with joints/articulations.
- Adding primitive, mesh, heightfield, SDF, or site geometry through public builder methods.
- Static, kinematic, and dynamic body setup.
- Forward/inverse kinematics helper calls such as `newton.eval_fk()` and `newton.eval_ik()`.
- Allocating `CollisionPipeline`, contacts, state buffers, and control buffers.
- Replicating worlds with `ModelBuilder.replicate()` and reasoning about `world_count`.
- CPU/CUDA device selection through Warp for small smoke checks.
- Fixing no-contact or stale-state issues in a basic loop.

## Route elsewhere

- Solver choice, MuJoCo/Kamino/VBD/MPM/coupled solver behavior, or contact tuning: use `../solvers-contacts/SKILL.md`.
- URDF, MJCF, USD, mesh file import, schema resolvers, or asset conversion: use `../asset-import-export/SKILL.md`.
- Actuators, controller objects, IK objective workflows, and `ArticulationView`: use `../robotics-control/SKILL.md`.
- Sensors, viewers, example CLI, recording, and visualization: use `../sensors-visualization/SKILL.md`.

## Read order

1. `references/api-reference.md` for verified public constructors and core method signatures.
2. `references/workflows.md` for minimal loops, world replication, body/joint patterns, and validation order.
3. `references/troubleshooting.md` for import/device, stale FK, target-layout, contact-capacity, and validation failures.
4. `scripts/build_minimal_scene.py` when you need a safe, runnable public-API smoke test.

## Core loop checklist

1. Set global compatibility switches, such as `newton.use_coord_layout_targets = True`, before constructing a `ModelBuilder` when joint position targets are involved.
2. Build or replicate the model with public `ModelBuilder` methods.
3. Finalize the builder into a `Model`, optionally passing a Warp device string.
4. Allocate two `State` buffers, one `Control`, one `CollisionPipeline`, and a `Contacts` buffer from the pipeline.
5. Call `newton.eval_fk(model, model.joint_q, model.joint_qd, state)` before maximal-coordinate solvers or collision checks when generalized coordinates define the initial pose.
6. Per substep: clear forces, collide, solver-step, then swap state buffers.
7. Validate counts and array shapes before tuning physics.

## Minimal safe smoke

From this sub-skill directory, run:

```bash
python scripts/build_minimal_scene.py --device cpu --steps 3
```

Use `--device cuda:0` only after the root `scripts/check_newton_env.py --require-cuda` succeeds. The script prints body/shape/joint counts and the final `body_q` shape; it does not download assets or open a viewer.

## Operating rules

- Use public imports only: `import newton`, `import newton.geometry`, and `import warp as wp`.
- Do not teach future users to import from `newton._src`; private modules are implementation evidence, not runtime API.
- Prefer small checks on CPU first, then repeat on CUDA only when the task requires acceleration.
- Treat `ModelBuilder.finalize()` validation warnings as actionable evidence; do not hide them by using broad `skip_validation_*` flags unless the task explicitly asks for advanced recovery.
- Keep model construction and solver tuning separate: prove the scene has the expected bodies, joints, shapes, worlds, and contacts before changing solver parameters.
