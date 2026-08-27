# Physics troubleshooting

Use this guide to diagnose Kaolin Simplicits, material, scene, Warp/CUDA, and
experimental Newton coupling issues without reopening the original repository.
Start with the bundled backend probe when a failure involves imports, devices, or
optional packages.

```bash
python scripts/physics_backend_probe.py --json
python scripts/physics_backend_probe.py --require-cuda --json
python scripts/physics_backend_probe.py --require-cuda --require-newton --json
```

## Quick triage matrix

| Symptom | Likely cause | Safe action |
|---|---|---|
| `ModuleNotFoundError: warp` or `No module named warp` | Warp is missing; Simplicits scene/material kernels import it | Install a Kaolin-compatible environment with Warp, or keep to dry planning/CPU tensor validation. |
| `torch.cuda.is_available()` is false | CPU-only PyTorch, driver mismatch, or no visible GPU | Do not run scene stepping; use plan-only or CPU shape checks. |
| `SimplicitsScene()` later fails on device operations | Default scene device is `"cuda"`; input tensors or environment are CPU-only | Create tensors on the same CUDA device or avoid simulation until CUDA is ready. |
| `ModuleNotFoundError: newton` | Experimental Newton bridge optional dependency is absent | Use ordinary Simplicits path or gate Newton coupling behind installing/validating `newton`. |
| Shape assertion for `yms`, `prs`, or `rhos` | Material tensor is not `(N,)` | Squeeze `(N,1)` to `(N,)` or pass scalar values. |
| Shape assertion for `pts` | Points are not `(N, 3)` | Route geometry/sampling to produce 3D point samples. |
| Infinite/huge material response | `prs` too close to `0.5` causing Lame `lambda` singularity | Use physically plausible `prs < 0.5`, often `0.3-0.49` depending material. |
| `bake() requires either num_qps or sampling_indices` | Baking called without a sampling request | Pass `num_qps` or explicit `sampling_indices`. |
| `'num_qp' must be provided with SimplicitsObject` | Scene is adding an unbaked object | Pass bounded `num_qp`, or pre-bake to `SkinnedPhysicsPoints`. |
| `'renderable_pts' are not supported for already baked...` | Baked object already owns optional renderable weights | Omit `renderable_pts` or rebuild baked object with renderable points. |
| `Forces need to be set` | `run_sim_step()` called before any force/collision setup | Call gravity, floor, boundary, or collision setup after adding objects. |
| `Cannot prepare simulation for an empty scene` | Force setup before adding objects | Add at least one object first. |
| `Cannot add object after a force is set` | Scene constants already built for forces | Recreate/reset workflow: add all objects first, then set forces/collisions. |
| Rendered point query fails | Object has no renderable points/weights | Add `renderable_pts` with `SimplicitsObject` or use a baked object with `renderable`. |
| Collision misses or memory spikes | Contact radius/count not matched to scale | Tune radius/detection ratio/max pairs and reduce `num_qp` for smoke. |
| Newton solve unstable or slow | Time step, stiffness, collision penalty, or conditioning | Lower `timestep`, lower penalties/stiffness, increase regularizer, use QR/normalization defaults, or reduce object complexity. |

## Backend failures

### Warp import or initialization failure

Simplicits scene, materials, sparse matrices, and many force/collision kernels
use Warp. Even when you only construct `PhysicsPoints`, importing the public
Simplicits package may transitively import Warp-backed modules.

Actions:

1. Run the probe without requiring CUDA to distinguish import failure from GPU
   failure.
2. If Warp import fails, stop at dry planning; do not attempt scene stepping.
3. Confirm the Kaolin/PyTorch/Warp versions come from a compatible install set.
4. Avoid source-build assumptions unless a CUDA toolkit and compiler are known
   available.

### CUDA unavailable or wrong device

Practical `SimplicitsScene.run_sim_step()` should be treated as CUDA/Warp-gated.
Common issues:

- CPU-only PyTorch installed.
- GPU hidden by environment configuration.
- Tensors on CPU while `SimplicitsScene(device="cuda")` expects CUDA.
- Mixed devices across `pts`, material tensors, `init_transform`, and force
  vectors.

Actions:

```python
assert torch.cuda.is_available()
device = "cuda"
pts = pts.to(device=device, dtype=torch.float32)
physics_points = physics_points.to(device)
scene = kaolin.physics.simplicits.SimplicitsScene(device=device)
```

For dry planning, explicitly say that CPU construction checks are not proof of
simulation readiness.

### Optional Newton import failure

`kaolin.experimental.newton` imports the optional `newton` package. If it is not
installed, importing the bridge can fail before any classes are available.

Actions:

- Keep the workflow on ordinary `kaolin.physics.simplicits` unless Newton
  coupling is explicitly required.
- If Newton coupling is required, run the probe with `--require-newton`.
- Treat successful import as a gate, not as proof that long rigid/MPM/robot
  notebooks will run.

## Tensor and data-contract failures

### `PhysicsPoints` material shape errors

Correct construction:

```python
N = pts.shape[0]
yms = torch.full((N,), 1.0e5, device=pts.device, dtype=pts.dtype)
prs = torch.full((N,), 0.45, device=pts.device, dtype=pts.dtype)
rhos = torch.full((N,), 500.0, device=pts.device, dtype=pts.dtype)
physics_points = kaolin.physics.simplicits.PhysicsPoints(
    pts=pts, yms=yms, prs=prs, rhos=rhos, appx_vol=torch.tensor(1.0, device=pts.device, dtype=pts.dtype)
)
```

If user data has `(N, 1)` material tensors:

```python
yms = yms.reshape(-1)
prs = prs.reshape(-1)
rhos = rhos.reshape(-1)
```

Then verify all three have length `N`.

### Bad Poisson ratio or Lame conversion

`to_lame(yms, prs)` computes `lam` with denominator `(1 - 2 * prs)`. Values
near `0.5` can explode; values at `0.5` are singular.

Actions:

- Clamp or reject `prs >= 0.5` for simulation plans.
- For incompressible-looking materials, choose a value below `0.5` and lower the
  timestep/regularize the solve.
- Report units and material assumptions; do not silently change material values
  in final code without explaining.

### Baked object shape errors

For `SkinnedPhysicsPoints`, validate:

```python
assert baked.pts.shape == (N, 3)
assert baked.yms.shape == baked.prs.shape == baked.rhos.shape == (N,)
assert baked.skinning_weights.shape[0] == N
assert baked.dwdx.shape == (N, baked.skinning_weights.shape[1], 3)
assert baked.check_sanity(log_error=True)
```

If `renderable` exists, validate its point count independently; it does not need
to equal the quadrature point count, but its `skinning_weights` must have the
same handle dimension.

## Object-construction failures

### `create_rigid` old-API warnings

The preferred form is:

```python
sim_obj = kaolin.physics.simplicits.SimplicitsObject.create_rigid(
    physics_points=physics_points,
)
```

Old-style `pts=..., yms=..., prs=..., rhos=..., appx_vol=...` may still work but
emits a deprecation warning. Do not mix `physics_points` with old-style material
arguments.

### MLP training is slow or appears stuck

`create_with_mlp` can take minutes for realistic point counts and training
steps. It also uses loss computations and gradients that are backend-sensitive.

Actions:

- For smoke, set `training_num_steps` to a tiny value and `num_samples` to a
  bounded subset.
- Prefer `create_rigid` to test scene plumbing.
- Consider bounded RKPM when the goal is a basis rather than exercising the MLP.
- Make progress/log frequency explicit and warn that smoke training is not a
  quality result.

### RKPM/eigenanalysis memory or dtype issues

`create_with_rkpm` constructs a basis using nodes, sample points, and
linear-algebra steps. Large `num_nodes` or `num_points` can consume memory.

Actions:

- Start with small `num_handles`, `num_nodes`, and `num_points`.
- Use `dtype=torch.float64` for stability when budget allows; lower to
  `float32` only as a conscious speed/memory trade-off.
- If the object is poorly conditioned, try fewer points/nodes first to diagnose
  before scaling up.

### Custom skinning function returns the wrong handle count

A callable passed to `create_from_function` should return learned/non-constant
weights only. The constant handle is appended by `compute_skinning_weights`.

If you expect `H` total handles, `fcn(pts)` should return `(N, H-1)`.

## Scene setup and stepping failures

### Wrong object addition order

Correct order:

1. Create scene.
2. Add all objects.
3. Set gravity/floor/boundaries/collisions.
4. Run steps.
5. Query deformed points/transforms.

If a force was already set and you need to add another object, create a new
scene and re-add objects in the right order.

### `init_transform` or kinematic transform errors

Accepted transforms are 3x4 or 4x4 torch tensors. Non-tensor values or wrong
ranks raise errors.

- Use `set_object_initial_transform` only for non-kinematic objects and only
  before simulation starts.
- Use `set_kinematic_object_transform` for objects added with
  `is_kinematic=True`.
- Keep transforms on the scene device and dtype.

### Querying rendered points fails

`get_object_deformed_pts(obj_id, "rendered")` and
`get_object_point_transforms(obj_id, "rendered")` require renderable weights.
For unbaked `SimplicitsObject`, pass `renderable_pts` to `scene.add_object`. For
baked objects, include `renderable` inside the baked `SkinnedPhysicsPoints`.

Fallback: query `points="simulated"` to inspect quadrature point motion.

### Simulation unstable, NaNs, or non-convergence

Actions in increasing cost order:

1. Lower `timestep`.
2. Use fewer quadrature points and one object to reproduce.
3. Lower stiffness (`yms`), collision/floor/boundary penalties, or friction.
4. Increase `newton_hessian_regularizer`.
5. Increase `max_newton_steps` only after small-scene behavior is sane.
6. Keep `normalize_weights_by_samples=True` and `apply_qr=True` unless debugging
   a basis issue.
7. Compare `direct_solve=True` vs `False` with bounded `cg_iters`.

Document that low Newton-step settings are for interactive speed, not guaranteed
convergence.

## Collision-specific failures

### Contacts are missed

- `collision_particle_radius` too small for object scale.
- `detection_ratio` too low.
- `num_qp` too sparse.
- Kinematic/static states not updated before contact detection.

Actions: increase radius/detection ratio, use more quadrature points after smoke
passes, or verify deformed point positions before collision setup.

### Contact memory or hessian assembly is too large

- `max_contact_pairs` too high.
- Too many objects/points.
- Collision radius/detection ratio too broad.

Actions: reduce `num_qp`, reduce object count, lower contact cap, and tune the
radius to object scale.

## Newton coupling failures

### Import works but `finalize` or solver step fails

Likely causes:

- Simplicits objects were added without `num_qp`.
- Base Newton objects or solvers expect different device/state conventions.
- `contacts` not supplied where soft-rigid contacts are expected.
- A long example pattern mutates Newton model counts without restoring them.

Actions:

1. Start with one rigid Simplicits object and a ground plane.
2. Build model, create two states, call `model.collide(state_in)`, and run one
   `SimplicitsSolver.step`.
3. Add the other Newton solver only after the Simplicits step updates its
   particle slice.
4. Keep state swapping explicit: `state_in, state_out = state_out, state_in`.

### `requires_grad=True` warning

The builder warns that Simplicits is not differentiable yet and proceeds with
`requires_grad=False`. Do not promise differentiable Simplicits-Newton coupling.

## Output-routing failures

### User asks to save/display results

This sub-skill should supply tensors/transforms, not own the final output route.

- Mesh vertices: `get_object_deformed_pts(obj_id, "rendered")`.
- Gaussian transforms: `get_object_point_transforms(obj_id, "rendered")`.
- Baked physics state: `PhysicsPoints`/`SkinnedPhysicsPoints` for I/O owner.
- Frame sequences: hand tensors to visualization/Timelapse owner.

If USD, Timelapse, browser, or notebook dependencies fail, route to the relevant
sub-skill and keep physics debugging separate.

## Safe minimal repro template

Use this to reduce most physics issues before attempting full tutorials:

```python
import torch
import kaolin

assert torch.cuda.is_available(), "CUDA is required for this scene smoke"
device = "cuda"
pts = torch.rand(64, 3, device=device, dtype=torch.float32) - 0.5
physics_points = kaolin.physics.simplicits.PhysicsPoints(
    pts=pts, yms=1.0e4, prs=0.45, rhos=500.0, appx_vol=1.0
)
sim_obj = kaolin.physics.simplicits.SimplicitsObject.create_rigid(
    physics_points=physics_points
)
scene = kaolin.physics.simplicits.SimplicitsScene(device=device)
obj_id = scene.add_object(sim_obj, num_qp=32, renderable_pts=pts.clone())
scene.max_newton_steps = 1
scene.set_scene_gravity(acc_gravity=torch.tensor([0.0, 9.8, 0.0], device=device))
scene.run_sim_step()
print(scene.get_object_deformed_pts(obj_id, "rendered").shape)
```

If this fails, debug backend/device/shape first. If it passes, scale one axis at
a time: object size, samples, training method, forces, collisions, frames, then
output integration.
