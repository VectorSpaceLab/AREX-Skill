# Core modeling workflows

## Minimal scene loop

```python
import warp as wp
import newton

newton.use_coord_layout_targets = True
wp.init()
wp.set_device("cpu")

builder = newton.ModelBuilder(gravity=(0.0, 0.0, -9.81))
body = builder.add_body(xform=wp.transform((0.0, 0.0, 0.75), wp.quat_identity()), mass=1.0)
builder.add_shape_sphere(body, radius=0.25)
builder.add_ground_plane()
model = builder.finalize(device="cpu")

state0 = model.state()
state1 = model.state()
control = model.control()
pipeline = newton.CollisionPipeline(model)
contacts = pipeline.contacts()
solver = newton.solvers.SolverXPBD(model, iterations=4)

newton.eval_fk(model, model.joint_q, model.joint_qd, state0)
for _ in range(120):
    state0.clear_forces()
    pipeline.collide(state0, contacts)
    solver.step(state0, state1, control, contacts, 1.0 / 60.0)
    state0, state1 = state1, state0
```

Route solver alternatives and contact tuning to `../solvers-contacts/SKILL.md` after this loop shape is correct.

## Body/link choice

- Use `add_body()` for a free-floating rigid body that can stand alone.
- Use `add_link()` when building an articulation manually; each link needs a joint connection and the joint indices must be passed to `add_articulation()`.
- Root links may be static, kinematic, or dynamic depending on joint type and `is_kinematic`.
- Kinematic non-root links are invalid; use a kinematic root with dynamic descendants or a static fixed-root body.

## Static, kinematic, dynamic

- Static: world-attached fixed objects or fixed-root links with zero DOFs.
- Kinematic: root bodies/links moved by user state updates, not integrated from forces.
- Dynamic: default body/link behavior; solvers integrate forces, contacts, and constraints.

Validate this classification before blaming solver parameters.

## Articulation coordinates

Generalized coordinates live in `State.joint_q` and `State.joint_qd`; maximal coordinates live in `State.body_q` and `State.body_qd`. Solver families differ:

- Generalized-coordinate solvers include MuJoCo and Featherstone.
- Maximal-coordinate solvers include XPBD, SemiImplicit, VBD, and Kamino-like workflows.

Collision detection needs current body poses, so call `newton.eval_fk()` after writing generalized coordinates and before collision checks for maximal-coordinate workflows.

## Multi-world replication

Use a template builder, then replicate it into a scene builder:

```python
template = newton.ModelBuilder()
body = template.add_body(mass=1.0, label="body")
template.add_shape_box(body, hx=0.25, hy=0.25, hz=0.25)

scene = newton.ModelBuilder()
scene.replicate(template, world_count=16, spacing=(1.0, 1.0, 0.0))
model = scene.finalize()
```

When visualizing many worlds, route to `../sensors-visualization/SKILL.md` for `set_visible_worlds()` and viewer offsets.

## Contact pipeline allocation

`CollisionPipeline(model)` stores pipeline configuration. `pipeline.contacts()` creates a contacts buffer sized for the chosen model and pipeline. Allocate contacts once, reuse each step, and increase `rigid_contact_max` only after proving the scene geometry and filters are correct.

Typical substep order:

1. `state.clear_forces()`.
2. Apply controls, actuation, or external forces.
3. `pipeline.collide(state, contacts)`.
4. `solver.step(state, next_state, control, contacts, dt)`.
5. Swap states.

## Validation habits

- Print `model.body_count`, `model.shape_count`, `model.joint_coord_count`, `model.joint_dof_count`, and world counts for generated scenes.
- Inspect `state.body_q.numpy().shape` in smoke tests; `.numpy()` already synchronizes Warp work.
- Avoid disabling validation until a smaller scene proves the model is physically meaningful.
- Keep optional imports explicit. If asset files are needed, route to asset import/export rather than hiding file resolution in model-building code.
