---
name: solvers-contacts
description: "Choose and configure Newton solvers and contact/collision workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Newton solvers and contacts

Use this sub-skill when a task requires choosing a Newton solver, wiring a solver step loop, deciding whether to use `CollisionPipeline` or MuJoCo-native contacts, enabling SDF/hydroelastic contact generation, or tuning solver/contact behavior.

## Read order

1. `references/solver-selection.md` — solver feature/coordinate matrix, public constructor signatures, solver-step contracts, and solver routing rules.
2. `references/contact-and-tuning.md` — contact pipeline setup, MuJoCo contact routes, contact material fields, SDF/hydroelastic prerequisites, and tuning workflow.
3. `references/troubleshooting.md` — symptom-driven fixes for coordinate mismatches, missing optional dependencies, unsupported joints/geometries, contact capacity, SDF/hydroelastic setup, and determinism.
4. `scripts/compare_solver_step.py` — safe smoke helper for a tiny scene. It runs `SolverXPBD` by default and can try SemiImplicit, Featherstone, or MuJoCo when explicitly requested.

## Operating boundaries

- Use public APIs only: `import newton`, `newton.solvers.*`, `newton.CollisionPipeline`, and `newton.geometry.*` when needed. Do not import from `newton._src`.
- Route basic `ModelBuilder`, state/control allocation, and ordinary simulation-loop construction to the `modeling-simulation` sub-skill.
- Route URDF/MJCF/USD parsing and mesh preprocessing/import questions to `asset-import-export` before returning here for solver/contact choices.
- Route viewer, contact visualization, and sensor diagnostics to `sensors-visualization` after this sub-skill has identified which contacts or solver outputs must be observed.
- Treat MuJoCo, Kamino, VBD, coupled solvers, SDF, hydroelastic, and GPU-deterministic behavior as capability-specific choices that need explicit environment and feature checks.

## Default decision path

1. Identify the model type: free rigid bodies, generalized-coordinate robot, maximal-coordinate mechanism, particles/cloth/soft bodies, MPM material, or coupled multi-physics.
2. Identify the contact source:
   - Use `CollisionPipeline` for Newton-generated rigid/soft contacts, SDF contacts, hydroelastic contacts, contact matching, and deterministic contact ordering.
   - Use `SolverMuJoCo(..., use_mujoco_contacts=True)` for MuJoCo-native contacts when MuJoCo semantics are desired and advanced Newton contact models are not needed.
   - Use `SolverMuJoCo(..., use_mujoco_contacts=False)` plus `CollisionPipeline` when MuJoCo dynamics must consume Newton-generated contacts.
3. Start conservative: `SolverXPBD(model, iterations=5)` plus `CollisionPipeline(model)` is the safe default for tiny public Newton scenes unless the task specifically needs generalized coordinates, MuJoCo semantics, cloth/soft/MPM, Kamino loops, or coupled solvers.
4. Before tuning contact gains, verify geometry, collision groups/world indices, forward kinematics freshness, contact counts, buffer capacities, and the selected solver's feature support.

## Minimal public loop pattern

```python
import warp as wp
import newton

builder = newton.ModelBuilder(gravity=(0.0, 0.0, -9.81))
builder.add_ground_plane()
body = builder.add_body(xform=wp.transform(p=(0.0, 0.0, 0.55), q=wp.quat_identity()))
builder.add_shape_sphere(body, radius=0.5)
model = builder.finalize(device="cpu")

solver = newton.solvers.SolverXPBD(model, iterations=5)
state_in = model.state()
state_out = model.state()
control = model.control()
pipeline = newton.CollisionPipeline(model)
contacts = pipeline.contacts()

dt = 1.0 / 60.0 / 4
for _ in range(4):
    state_in.clear_forces()
    pipeline.collide(state_in, contacts)
    solver.step(state_in, state_out, control, contacts, dt)
    state_in, state_out = state_out, state_in
```

For a runnable version with diagnostics and fallback behavior, use `scripts/compare_solver_step.py`.
