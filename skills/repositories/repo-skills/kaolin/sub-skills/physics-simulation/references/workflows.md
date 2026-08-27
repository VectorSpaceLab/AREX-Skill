# Physics workflows

These workflows are bounded operating plans for Kaolin physics tasks. They avoid
asset downloads, notebook execution, browser launch, and long training by
default. Route geometry loading, sampling, USD/Timelapse output, and rendering to
the appropriate sibling sub-skills; this sub-skill owns the physics objects,
scene, backend checks, and simulation queries.

## Workflow 0: backend-gated planning

1. Classify the requested outcome:
   - **Plan only**: no backend run; provide code outline and gates.
   - **Construction smoke**: create `PhysicsPoints`/`SimplicitsObject` with tiny
     tensors; does not prove scene stepping.
   - **Simulation smoke**: requires CUDA/Warp and tiny `num_qp`/step count.
   - **Full tutorial/notebook**: likely expensive and optional-dependency gated.
   - **Experimental Newton coupling**: requires `newton`, Warp, and CUDA.
2. Run or suggest the bundled probe:

   ```bash
   python scripts/physics_backend_probe.py --json
   python scripts/physics_backend_probe.py --require-cuda --json
   python scripts/physics_backend_probe.py --require-cuda --require-newton --json
   ```

3. If CUDA/Warp is missing, stop at a dry plan or CPU shape validation. Do not
   promise `SimplicitsScene.run_sim_step()`.
4. If Newton is missing, keep Newton coupling as a plan with an install gate;
   still allow ordinary Simplicits planning when Warp/CUDA is available.
5. Bound any run: explicit object count, point count, `num_qp`, training steps,
   Newton steps, frame count, and outputs.

## Workflow 1: point samples to `PhysicsPoints`

Use when the user already has point-sampled geometry or another sub-skill will
produce it.

```python
import torch
import kaolin

pts = pts.to(device="cuda", dtype=torch.float32)  # shape (N, 3)
physics_points = kaolin.physics.simplicits.PhysicsPoints(
    pts=pts,
    yms=1.0e5,       # scalar expands to (N,)
    prs=0.45,        # keep below 0.5
    rhos=500.0,
    appx_vol=1.0,
)
assert physics_points.check_sanity(log_error=True)
```

Validation checklist:

- `pts.ndim == 2` and `pts.shape[1] == 3`.
- `yms`, `prs`, `rhos` are scalars or `(N,)` tensors; no `(N,1)` unless
  squeezed first.
- `appx_vol` is positive scalar-like; if it came from sampling, document the
  approximation.
- All tensors share device/dtype before simulation.
- Poisson ratio is comfortably below `0.5` to avoid singular Lame parameters.

When points come from a mesh or Gaussian, ask the relevant sub-skill to produce
surface/interior samples and an approximate volume estimate. Simplicits needs
volume-filling samples for high-quality elastic behavior; surface-only points
may be acceptable only for a cheap rigid/custom smoke.

## Workflow 2: choose object-construction mode

| Mode | Use when | Minimal call | Bound it |
|---|---|---|---|
| Rigid/single handle | Fast smoke, stiff object, coupling scaffold | `SimplicitsObject.create_rigid(physics_points=physics_points)` | Very cheap; use first when backend is uncertain. |
| Custom function | Deterministic weights, unit tests, known handle functions | `SimplicitsObject.create_from_function(physics_points, fcn)` | Ensure `fcn(points)` returns `(N, H-1)`; constant handle is appended. |
| MLP | Need learned Simplicits weights from the original method | `SimplicitsObject.create_with_mlp(...)` | Set small `training_num_steps` for smoke; full training may take minutes. |
| RKPM / FreeForm | Need faster basis construction and backend/memory allow it | `SimplicitsObject.create_with_rkpm(...)` | Bound `num_nodes`, `num_points`, and dtype. |
| Baked object | Weights already stored or loaded | use `SkinnedPhysicsPoints` directly | Avoid retraining; ensure `dwdx` and optional renderable weights exist. |

### Fast rigid/custom smoke

```python
sim_obj = kaolin.physics.simplicits.SimplicitsObject.create_rigid(
    physics_points=physics_points,
)
# Optional: bake a tiny quadrature subset for later scene use.
baked = sim_obj.bake(num_qps=min(64, len(physics_points)))
```

### Bounded MLP smoke

```python
sim_obj = kaolin.physics.simplicits.SimplicitsObject.create_with_mlp(
    physics_points=physics_points,
    num_handles=4,
    num_samples=min(256, len(physics_points)),
    model_layers=2,
    training_batch_size=16,
    training_num_steps=10,      # smoke only, not quality training
    training_lr_start=1e-3,
    training_lr_end=1e-3,
    training_log_every=10,
    normalize_for_training=True,
)
```

### Bounded RKPM plan

```python
sim_obj = kaolin.physics.simplicits.SimplicitsObject.create_with_rkpm(
    physics_points=physics_points,
    num_handles=8,
    num_nodes=64,
    num_points=min(512, len(physics_points)),
    dtype=torch.float64,
)
```

For production-quality elastic behavior, increase sample counts only after the
backend probe passes and the user accepts runtime/memory cost.

## Workflow 3: add one object to a Simplicits scene

```python
import torch
import kaolin

scene = kaolin.physics.simplicits.SimplicitsScene(device="cuda")
scene.timestep = 0.03
scene.max_newton_steps = 3       # small smoke; tune higher for quality
scene.newton_hessian_regularizer = 1e-4

obj_id = scene.add_object(
    sim_obj,
    num_qp=128,                  # required for SimplicitsObject
    renderable_pts=render_pts,   # optional (M, 3), e.g. mesh vertices or splat positions
    init_transform=torch.eye(4, device="cuda", dtype=torch.float32),
)
scene.set_scene_gravity(acc_gravity=torch.tensor([0.0, 9.8, 0.0], device="cuda"))
scene.set_scene_floor(floor_height=-0.8, floor_axis=1, floor_penalty=1000.0)

for _ in range(3):
    scene.run_sim_step()

simulated_pts = scene.get_object_deformed_pts(obj_id, points="simulated")
rendered_pts = scene.get_object_deformed_pts(obj_id, points="rendered")
per_point_tfms = scene.get_object_point_transforms(obj_id, points="rendered")
```

Scene setup rules:

- Add all objects before setting forces/collisions; adding after force setup is
  rejected.
- If `sim_obj` is a `SimplicitsObject`, pass `num_qp`. If it is already baked
  `SkinnedPhysicsPoints`, `num_qp` is optional and `renderable_pts` must be
  omitted.
- Call at least one force/collision setup before `run_sim_step()`; otherwise
  the scene is not ready for forces.
- `init_transform` is a standard 3x4 or 4x4 transform; the scene stores a
  relative transform internally.
- `points="rendered"` works only when renderable points/weights were provided.

## Workflow 4: mesh to physics, then route outputs

Use this when the user wants to simulate a mesh but the loading/sampling details
belong to other sub-skills.

1. Route mesh import, centering/scaling, material/texture handling, and mesh
   container details to `geometry-io-representations`.
2. Route sampling (`sample_points`, interior/volume sampling strategy, normals,
   approximate volume estimation) to `ops-metrics-conversions` when needed.
3. In this sub-skill, wrap the sampled points in `PhysicsPoints` with material
   tensors.
4. Start with `create_rigid` for a smoke test; use `create_with_rkpm` or
   `create_with_mlp` only after the backend and runtime budget are accepted.
5. Add the object to `SimplicitsScene` with `renderable_pts=mesh.vertices` if the
   caller later wants deformed mesh vertices.
6. After stepping, return `scene.get_object_deformed_pts(obj_id, "rendered")` or
   `scene.get_object_point_transforms(obj_id, "rendered")` to the visualization
   or geometry-output owner.

Bounded mesh smoke parameters:

- `N` physics samples: 128-1024 for smoke.
- `num_qp`: 64-256 for scene smoke.
- `max_newton_steps`: 1-5.
- Frames: 1-10.
- No full notebook rendering unless explicitly requested.

## Workflow 5: Gaussian/splat simulation plan

Gaussian splats are renderable points plus anisotropic attributes. Simplicits
simulates positions through point-sampled physics and supplies per-point
transforms to deform/render Gaussian attributes.

1. Route Gaussian import/container validation and USD/PLY fields to
   `geometry-io-representations`.
2. Route volume densification or sample selection to `ops-metrics-conversions`.
   Surface Gaussian centers alone often undersample the interior.
3. Build `PhysicsPoints` from densified/in-volume points and material tensors.
4. Build a `SimplicitsObject` (prefer rigid or bounded RKPM first).
5. When adding to the scene, pass Gaussian positions as `renderable_pts` so
   renderable weights are baked:

   ```python
   obj_id = scene.add_object(
       sim_obj,
       num_qp=2048,
       renderable_pts=gaussians.positions,
   )
   ```

6. Each frame, query transforms:

   ```python
   per_splat_tfms = scene.get_object_point_transforms(obj_id, points="rendered")
   ```

7. Route application of transforms to Gaussian positions/orientations/scales and
   final visualization/export to the visualization or geometry I/O sub-skills.

Safe default: plan the flow and validate tensor shapes without training; only
run a tiny rigid scene smoke if CUDA/Warp is confirmed.

## Workflow 6: load/use baked `SkinnedPhysicsPoints`

Use when weights and `dwdx` are already present, or another workflow saved a
baked physics object.

```python
# baked: kaolin.physics.simplicits.SkinnedPhysicsPoints
scene = kaolin.physics.simplicits.SimplicitsScene(device="cuda")
obj_id = scene.add_object(baked, num_qp=None)
scene.set_scene_gravity(acc_gravity=torch.tensor([0.0, 9.8, 0.0], device="cuda"))
scene.run_sim_step()
```

Rules:

- Do not pass `renderable_pts` when adding baked `SkinnedPhysicsPoints`; the
  optional renderable set must already be inside `baked.renderable`.
- If you need fewer quadrature points, `num_qp` can subsample the baked object.
- Check `baked.check_sanity(log_error=True)` before scene insertion.
- Use baked objects to avoid long MLP/RKPM training in repeated workflows.

## Workflow 7: forces, boundaries, collisions, and kinematic objects

### Gravity and floor

```python
scene.set_scene_gravity(acc_gravity=torch.tensor([0.0, 9.8, 0.0], device=scene.device))
scene.set_scene_floor(floor_height=-0.8, floor_axis=1, floor_penalty=1000.0)
```

Tune by object scale. If an object shoots away or penetrates the floor, reduce
`timestep`, increase `max_newton_steps`, adjust `floor_penalty`, or regularize
more.

### Boundary condition

```python
def pin_left(points):
    return points[:, 0] < points[:, 0].min() + 0.05

pinned_positions = scene.set_object_boundary_condition(
    obj_id,
    name="pin_left",
    fcn=pin_left,
    bdry_penalty=10000.0,
)
```

The selector receives current deformed points for that object and must return a
1D boolean mask.

### Collisions

```python
scene.enable_collisions(
    collision_particle_radius=0.05,
    detection_ratio=1.5,
    impenetrable_barrier_ratio=0.25,
    collision_penalty=1000.0,
    max_contact_pairs=10000,
    friction=0.5,
)
```

Tune `collision_particle_radius` to object scale. If contacts are missed, raise
`detection_ratio` or `max_contact_pairs`; if memory spikes, lower contact count
or quadrature points.

### Kinematic object

```python
kin_id = scene.add_object(sim_obj, num_qp=128, is_kinematic=True)
scene.set_scene_gravity()
scene.set_kinematic_object_transform(kin_id, transform)
```

Kinematic objects have handles but are not solved dynamically. Use
`set_kinematic_object_transform` rather than `set_object_initial_transform` for
motion during simulation.

## Workflow 8: experimental Newton coupling

Use only when the user explicitly requests Newton integration and the probe
confirms `newton`, Warp, and CUDA. Keep a warning that the API is experimental.

```python
import torch
import newton
from kaolin.experimental.newton.builder import SimplicitsModelBuilder
from kaolin.experimental.newton.solver import SimplicitsSolver

builder = SimplicitsModelBuilder(up_axis="y", gravity=-9.81)
builder.add_simplicits_object(
    sim_obj,
    num_qp=512,
    init_transform=torch.eye(4, device="cuda", dtype=torch.float32),
    renderable_pts=render_pts,
)
builder.add_simplicits_collisions(collision_particle_radius=0.05)
# Add Newton rigid/articulated/MPM objects through Newton builder APIs here.
model = builder.finalize(device="cuda")

solver = SimplicitsSolver(model)
state_in = model.state()
state_out = model.state()

for _ in range(3):
    contacts = model.collide(state_in)
    solver.step(state_in, state_out, control=None, contacts=contacts, dt=1.0 / 60.0)
    state_in, state_out = state_out, state_in
```

Coupling notes:

- `SimplicitsModelBuilder` extends Newton's builder; base Newton objects are
  added with Newton APIs.
- `SimplicitsSolver` updates only the Simplicits particle slice and reduced
  DOFs; other Newton solvers may need to step in sequence for rigid bodies,
  articulations, or MPM.
- Some examples temporarily mutate Newton model counts so a solver skips a
  particle/body family; preserve this only with a clear reason and small scope.
- Contacts passed into `SimplicitsSolver.step` enable soft-rigid contact energy.
- Treat long robot/MPM notebooks as demonstration plans, not default tests.

## Workflow 9: routing output to USD/Timelapse or rendering

This sub-skill returns physics state, not presentation artifacts.

- For mesh-like output, provide deformed renderable vertices from
  `get_object_deformed_pts(obj_id, "rendered")` to the visualization or I/O
  owner.
- For Gaussian output, provide per-point transforms from
  `get_object_point_transforms(obj_id, "rendered")` and route attribute updates
  to the Gaussian/rendering owner.
- For baked physics persistence, pass `PhysicsPoints` and `SkinnedPhysicsPoints`
  objects to the geometry I/O owner for USD-specific handling.
- For frame logs, pass per-frame tensors/meshes to `visualization-workflows` for
  Timelapse or notebook display.

## Suggested hard usability cases

Use these later for verification, not as runtime artifacts:

1. **Backend/shape diagnosis:** Given code that constructs `PhysicsPoints` with
   `yms` shaped `(N, 1)`, uses `prs=0.5`, then creates `SimplicitsScene()` on a
   CPU-only machine, diagnose every failure gate and produce a corrected bounded
   dry-run plan.
2. **Mesh/Gaussian bounded plan:** Given a mesh and Gaussian splat object, plan
   a no-long-training path: route input sampling, create `PhysicsPoints`, choose
   rigid or small RKPM construction, bake renderable Gaussian positions, run at
   most a few scene steps if CUDA/Warp probes pass, and route output to
   USD/Timelapse owners.
