# Modeling and simulation troubleshooting

## `ModuleNotFoundError: warp` or `ModuleNotFoundError: newton`

Install the base package first. For ordinary package usage:

```bash
pip install newton
```

For examples, viewers, importers, or development workflows, install only the needed extra from the root install reference.

## CUDA device is not usable

Symptoms include Warp device errors, CUDA initialization failures, or `cuda:0` unavailable.

1. Run the root `scripts/check_newton_env.py --show-optional`.
2. If CPU is acceptable, rerun the model smoke with `--device cpu`.
3. If CUDA is required, verify NVIDIA driver visibility with the user's platform tools and that Warp can allocate on `cuda:0`.
4. Do not treat a CPU pass as proof of CUDA performance or RTX viewer availability.

## No contacts are produced

Likely causes:

- `newton.eval_fk()` was not called after changing generalized coordinates.
- `CollisionPipeline.collide(state, contacts)` was not called before `solver.step()`.
- The shape pair is filtered, in different worlds, static/kinematic only, or outside the collision margin.
- `rigid_contact_max` or shape-pair buffers are too small for a dense scene.
- Mesh/SDF/hydroelastic prerequisites belong to the solver/contact route.

Start by reducing the scene to one dynamic sphere and one ground plane, then use `scripts/build_minimal_scene.py`.

## Deprecation warning for `joint_target_q`

Newton development builds warn when the legacy DOF-shaped position-target layout can misalign with free, ball, or distance joints. For new code, set:

```python
newton.use_coord_layout_targets = True
```

before creating a `ModelBuilder`. Then index position targets with coordinate starts and velocity/force targets with DOF starts.

## `ValueError` during `ModelBuilder.finalize()`

Common causes include invalid inertia, non-root kinematic links, malformed joint ordering, missing articulation grouping, invalid mesh topology, or inconsistent world structure.

Recovery steps:

1. Reproduce with one world and one body/joint.
2. Keep validation enabled and read the exact message.
3. Check body mass/inertia and whether `lock_inertia` is appropriate.
4. For imported assets, route to asset import/export because parsing flags can change topology.
5. Avoid `skip_all_validations=True` unless the user explicitly needs to inspect a known-invalid model.

## Simulation explodes or contains NaNs

- Confirm the model starts with finite arrays.
- Use a smaller `dt` or more substeps.
- Check mass/inertia scales, collision overlap at initialization, and contact material stiffness/damping.
- Switch to a simpler solver/contact route before tuning advanced solver parameters.
- Inspect arrays with `.numpy()` after the step; no explicit `wp.synchronize()` is needed before `.numpy()`.
