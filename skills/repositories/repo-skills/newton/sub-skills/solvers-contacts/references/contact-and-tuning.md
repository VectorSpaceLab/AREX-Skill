# Contacts, collision, and tuning

## CollisionPipeline versus MuJoCo-native contacts

Newton has a public `CollisionPipeline` with broad phase, narrow phase, contact reduction, SDF, hydroelastic, contact matching, and optional deterministic behavior. It produces `Contacts` buffers consumed by compatible solvers.

MuJoCo workflows have two contact routes:

- `SolverMuJoCo(..., use_mujoco_contacts=True)`: MuJoCo/MuJoCo Warp generates contacts internally. Use this when native MuJoCo semantics are desired and Newton-specific SDF/hydroelastic contact is not needed.
- `SolverMuJoCo(..., use_mujoco_contacts=False)`: Newton's `CollisionPipeline` generates contacts and MuJoCo dynamics consume them. Use this for SDF mesh contacts, hydroelastic contacts, or contact matching that MuJoCo-native contacts do not cover.

## Contact pipeline pattern

```python
pipeline = newton.CollisionPipeline(model, broad_phase="explicit")
contacts = pipeline.contacts()

for _ in range(substeps):
    state.clear_forces()
    pipeline.collide(state, contacts)
    solver.step(state, next_state, control, contacts, dt)
    state, next_state = next_state, state
```

Use `broad_phase="explicit"` as a safe default for many small/medium scenes. Consider `"sap"` or `"nxn"` only after profiling and correctness checks.

## Contact material fields

`ModelBuilder.ShapeConfig` and model material arrays store solver-neutral fields such as friction, stiffness/damping, restitution, torsional/rolling friction, and hydroelastic stiffness. Solvers consume different subsets:

- XPBD: restitution and several rigid/soft contact relaxation parameters.
- SemiImplicit and Featherstone: force-style friction and contact gains.
- MuJoCo: maps Newton force-space gains to MuJoCo contact parameters, with special handling for `use_mujoco_contacts` and raw MuJoCo custom attributes.
- VBD: AVBD/VBD rigid and particle contact parameters.
- Style3D and ImplicitMPM: material-specific particle/cloth/MPM parameters.

Before tuning gains, verify geometry, scale, mass/inertia, units, and contact count.

## SDF and hydroelastic contacts

SDF and hydroelastic contacts are geometry-preparation features, not just solver flags.

Checklist:

1. Mesh or primitive SDF data must be built or configured before collision.
2. Hydroelastic contacts require SDFs on both shapes in a pair.
3. SDF resolution, margin, and contact reduction affect performance and contact count.
4. `CollisionPipeline` must be used; MuJoCo-native contacts will not provide Newton hydroelastic behavior.
5. Contact buffers may need larger capacities for SDF/hydroelastic scenes.

Route mesh creation/remeshing/import questions to `../asset-import-export/SKILL.md`.

## Tuning order

1. Confirm model scale, gravity, masses, inertias, and initial overlap.
2. Confirm coordinate representation and FK freshness.
3. Confirm contact count and shape pair filtering.
4. Reduce `dt` or increase substeps.
5. Increase solver iterations/relaxation conservatively.
6. Tune material stiffness/damping/friction.
7. Enable advanced SDF/hydroelastic/contact matching only after a primitive-scene baseline works.
8. Re-run a tiny smoke when changing device or optional extras.

## Determinism and backend notes

- GPU reductions, contact ordering, graph capture, and solver-specific deterministic modes can affect reproducibility.
- Prefer task-level tolerances over exact bitwise comparisons unless deterministic mode is explicitly requested and verified.
- CPU smoke checks prove API viability, not CUDA performance or all GPU determinism.
