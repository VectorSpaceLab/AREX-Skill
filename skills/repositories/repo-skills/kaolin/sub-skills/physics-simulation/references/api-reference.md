# Physics API reference

This reference summarizes the Kaolin physics surface needed for operating tasks.
It is intentionally self-contained and omits repository/test paths. All tensors
mentioned here should live on the same device and generally share floating dtype
unless explicitly noted.

## Backend and dependency model

| Capability | Imports | Runtime expectation | Notes |
|---|---|---|---|
| Physics tensor containers | `torch`, `kaolin.physics.simplicits` | CPU construction can work when imports succeed | Useful for validating shapes and material values before CUDA work. |
| Simplicits object training/baking | `kaolin.physics.simplicits`, Warp transitively | Training can be expensive; RKPM/MLP usually planned for CUDA | `create_rigid` and custom functions are quickest for smoke plans. |
| Simplicits scene stepping | `warp`, `scipy`, CUDA-capable PyTorch | Treat CUDA/Warp as required for practical simulation | Default scene device is `"cuda"`; do not promise runs from CPU-only probes. |
| Materials/common forces | `kaolin.physics.materials`, `kaolin.physics.common` | Warp arrays and kernels are used for simulation energies | Some pure Torch formulas are testable, but scene use is Warp-backed. |
| Experimental Newton coupling | `kaolin.experimental.newton`, `newton`, `warp` | Optional, experimental, version-sensitive | Import fails if `newton` is not installed; keep as gated path. |

Use `scripts/physics_backend_probe.py` to check imports, CUDA availability,
Warp, and optional Newton readiness without launching a simulation by default.

## Point-sampled physics data

### `PhysicsPoints(pts, yms, prs, rhos, appx_vol, strict_checks=True)`

Container for simulation quadrature/sample points plus material parameters.

| Field | Shape / accepted input | Units / meaning | Common pitfalls |
|---|---|---|---|
| `pts` | `(N, 3)` floating tensor | Object sample points in meters | Must be rank 2 with exactly 3 columns. |
| `yms` | scalar or `(N,)` tensor | Young's modulus, stiffness | Tensor must match `N`; scalar is expanded. |
| `prs` | scalar or `(N,)` tensor | Poisson ratio | Avoid values at or above `0.5`; Lame conversion divides by `1 - 2*prs`. |
| `rhos` | scalar or `(N,)` tensor | Density | Tensor must match `N`; scalar is expanded. |
| `appx_vol` | float, scalar tensor, or length-1 tensor squeezed to scalar | Approximate object volume | Keep positive and on same dtype/device after construction. |

Useful members:

- `subsample(num_pts=None, sample_indices=None)` returns another
  `PhysicsPoints`. Choose exactly one of `num_pts` or `sample_indices`.
- `check_sanity(log_error=True)` validates tensor attributes.
- `.device`, `.dtype`, `len(obj)` reflect `pts`.
- `.to()`, `.cuda()`, `.cpu()` are inherited from the tensor-container base.

### `SkinnedPoints(pts, skinning_weights, strict_checks=True)`

Renderable or auxiliary point set plus precomputed skinning weights.

| Field | Shape | Meaning |
|---|---|---|
| `pts` | `(M, 3)` | Points to deform for rendering/output, not necessarily quadrature points. |
| `skinning_weights` | `(M, H)` | Per-point weights for `H` handles. |

Use `SkinnedPoints.from_skinning_mod(pts, skinning_mod)` to bake renderable
weights from a `SkinningModule`.

### `SkinnedPhysicsPoints(...)`

Baked simulation-ready object: `PhysicsPoints` fields plus skinning data.

| Field | Shape | Meaning |
|---|---|---|
| `pts` | `(N, 3)` | Quadrature/sample points. |
| `yms`, `prs`, `rhos` | `(N,)` | Per-point material values. |
| `appx_vol` | scalar-like | Total approximate volume. |
| `skinning_weights` | `(N, H)` | Weights used by the reduced LBS basis. |
| `dwdx` | `(N, H, 3)` | Jacobian of weights with respect to rest position. |
| `renderable` | `SkinnedPoints` or `None` | Optional separate renderable points. |

Factories and methods:

- `SkinnedPhysicsPoints.from_skinning_mod(pts, yms, prs, rhos, appx_vol,
  skinning_mod, renderable_pts=None)` computes `skinning_weights`, `dwdx`, and
  optional renderable weights.
- `subsample(num_pts=None, sample_indices=None)` keeps the same total
  `appx_vol` while slicing per-point fields.

## Skinning modules and Simplicits objects

### `SkinningModule(bb_min=None, bb_max=None)`

Base class for skinning weight functions. It normalizes points from the supplied
bounding box and appends an implicit constant handle.

- `compute_skinning_weights(pts)` returns `(N, H)` where the last handle is the
  constant `1` handle.
- `compute_dwdx(pts)` returns `(N, H, 3)`. It uses a custom `grad` method when
  present, otherwise `torch.func.jacrev`/`vmap`.
- `SkinningModule.from_function(function, bb_min=0, bb_max=1)` wraps a callable
  that returns only the learned/non-constant weights; the constant handle is
  appended by `compute_skinning_weights`.

### `SimplicitsMLP(spatial_dimensions, layer_width, num_handles, num_layers, bb_min=None, bb_max=None)`

ELU MLP skinning model. `num_handles` includes the implicit constant handle, so
its final layer emits `num_handles - 1` learned weights.

### `SimplicitsObject(pts, yms, prs, rhos, appx_vol, skinning_mod)`

Object carrying point-sampled materials and a skinning module. It can be trained,
constructed analytically, baked, then added to a scene.

Factories:

| Factory | Signature shape | Use when | Cost / notes |
|---|---|---|---|
| `create_rigid(physics_points=...)` | new API; old `pts/yms/prs/rhos/appx_vol` emits a deprecation warning | Need a very fast single-handle object or stiff near-rigid behavior | `num_handles == 1`; constant weight equals 1. |
| `create_with_mlp(physics_points, num_handles, num_samples, model_layers, ...)` | training hyperparameters include batch size, steps, LR, loss coefficients | Need learned Simplicits weights | Expensive; if `num_handles == 1`, falls back to rigid with warning. |
| `create_with_rkpm(physics_points, num_handles, num_nodes, num_points=None, dtype=torch.float64)` | RKPM/FreeForm basis | Prefer this for faster basis construction when backend/memory allow | Uses eigenanalysis; `dtype=float64` default improves stability. |
| `create_from_function(physics_points, fcn)` | callable or `SkinningModule` | Need custom weights or a deterministic smoke object | Callable output excludes constant handle. |
| `create_trained(...)` | legacy old-style args | Existing code only | Deprecated; route to `create_with_mlp`. |

Methods:

- `to(*args, attributes=None, **kwargs)` also moves/casts `skinning_mod` unless
  `attributes` restricts conversion.
- `subsample(num_pts=None, sample_indices=None)` slices material points while
  sharing the same `skinning_mod`.
- `bake(num_qps=None, sampling_indices=None, renderable_pts=None)` returns
  `SkinnedPhysicsPoints`. One of `num_qps` or `sampling_indices` is required.
- `bake_for_rendering(renderable_pts)` returns `SkinnedPoints` only.

## Simplicits scene and simulation state

### `SimplicitsScene(device="cuda", direct_solve=True, use_cuda_graphs=False, timestep=0.03, max_newton_steps=5, max_ls_steps=10, newton_hessian_regularizer=1e-4, cg_tol=1e-4, cg_iters=100, conv_tol=1e-4)`

Reduced-coordinate scene. It owns objects, sparse matrices, Warp arrays, forces,
collisions, and Newton-step parameters.

Important attributes:

| Attribute | Meaning | Tuning note |
|---|---|---|
| `device` | Torch/Warp device string | Defaults to CUDA. Match all input tensors. |
| `timestep` | Seconds per scene step | Smaller values can stabilize stiff/collision scenes. |
| `direct_solve` | Direct linear solve vs CG path | Direct solve can be robust but memory-heavy. |
| `max_newton_steps`, `max_ls_steps` | Nonlinear solve limits | Low values are fast but may not converge. |
| `newton_hessian_regularizer` | Hessian regularization | Increase for ill-conditioned systems. |
| `cg_tol`, `cg_iters`, `conv_tol` | Iterative/convergence controls | Relevant when direct solve is disabled or convergence is poor. |

Scene methods:

| Method | Key inputs | Use / behavior | Pitfalls |
|---|---|---|---|
| `add_object(sim_object, num_qp=None, init_transform=None, is_kinematic=False, renderable_pts=None, normalize_weights_by_samples=True, apply_qr=True)` | `SimplicitsObject` or `SkinnedPhysicsPoints` | Bakes/subsamples object, creates internal `SimulatedObject`, returns integer id | `SimplicitsObject` requires `num_qp`; baked objects cannot also take `renderable_pts`. |
| `set_scene_gravity(acc_gravity=torch.tensor([0, 9.8, 0]), gravity_coeff=1.0)` | gravity vector | Adds point-wise gravity | Requires at least one object. |
| `set_scene_floor(floor_height=0.0, floor_axis=1, floor_penalty=10000.0, flip_floor=False)` | plane configuration | Adds penalty floor | Floor axis is 0/1/2. |
| `set_object_boundary_condition(obj_idx, name, fcn, bdry_penalty=10000.0, pinned_x=None)` | boolean selector over deformed points | Pins selected points using a penalty | `fcn` must return a 1D boolean mask over current object points. |
| `enable_collisions(collision_particle_radius=0.1, detection_ratio=1.5, impenetrable_barrier_ratio=0.25, collision_penalty=1000.0, max_contact_pairs=10000, friction=0.5)` | collision parameters | Enables self/inter-object collision energy | Tune radius/contact-pair count to object scale and memory. |
| `run_sim_step()` | none | Runs one Newton solve and increments `current_sim_step` | Fails until forces/collisions prepare the scene. |
| `reset_scene()` | none | Resets state, current step, and scene variables | Use before changing initial transforms or replaying. |
| `set_object_initial_transform(object_id, init_transform)` | 3x4 or 4x4 standard transform | Sets a non-kinematic object's initial transform before stepping | Cannot be called after simulation has started. |
| `set_kinematic_object_transform(obj_idx, transform)` | 3x4 or 4x4 standard transform | Updates kinematic object during simulation | Only for objects added with `is_kinematic=True`. |
| `get_object(obj_idx)` | id | Returns internal `SimulatedObject` | Internal object includes state and sparse matrices. |
| `get_object_transforms(object_id)` | id | Returns `(H, 4, 4)` relative transforms in raw physical space | Use with unnormalized renderable weights. |
| `get_object_deformed_pts(obj_idx, points="simulated" | "rendered")` | id and point set | Returns deformed quadrature or renderable points | `"rendered"` requires `renderable_pts`/`renderable`. |
| `get_object_point_transforms(obj_idx, points="simulated" | "rendered")` | id and point set | Returns per-point `(P, 4, 4)` transforms | Useful for deforming Gaussian attributes or external renderables. |

`init_transform` arguments are standard transforms; the scene converts them to
relative transforms internally by subtracting identity from the affine block.

## Materials, common forces, and utilities

### `kaolin.physics.materials.material_utils.to_lame(yms, prs)`

Converts Young's modulus and Poisson ratio to Lame coefficients:

- `mu = yms / (2 * (1 + prs))`
- `lam = yms * prs / ((1 + prs) * (1 - 2 * prs))`

Keep `prs < 0.5` to avoid singular or explosive `lam`.

### `kaolin.physics.materials.material_utils.get_defo_grad(wp_z, wp_dFdz)`

Builds Warp `mat33` deformation gradients from reduced coordinates and sparse
`dFdz`, adding identity to each gradient. This is an internal material/scene
utility for energy assembly, not a general tensor conversion routine.

### `NeohookeanElasticMaterial(mu, lam, integration_pt_volume, reparameterize_lame=False)`

Warp-backed material object used by Simplicits scenes.

| Method | Input | Output | Notes |
|---|---|---|---|
| `energy(defo_grads, coeff=1.0, wp_energy=None)` | Warp `mat33` array | Warp scalar energy accumulator | Allocates one scalar if not provided. |
| `gradient(defo_grads, coeff=1.0, gradients=None)` | Warp `mat33` array | Warp `mat33` gradient array | Can reuse output buffer. |
| `hessian(defo_grads, coeff=1.0)` | Warp `mat33` array | Warp `mat99` hessian blocks | Uses preallocated hessian block buffer. |

The module also exposes Torch reference formulas for testing, but the public
class is Warp-backed.

### Common force/collision objects

- `Gravity(g, integration_pt_density, integration_pt_volume)`: point-wise
  gravity energy/gradient.
- `Floor(floor_height, floor_axis, flip_floor, integration_pt_volume)`: floor
  penalty energy/gradient/hessian.
- `Boundary(integration_pt_volume)`: supports `set_pinned(indices, pinned_x)`
  then boundary energy/gradient/hessian.
- `Collision(...)`: detects particle contacts, computes collision Jacobian,
  bounds, energy, gradient, and hessian. In normal use, configure it through
  `SimplicitsScene.enable_collisions`.

### Utility helpers

| Helper | Role |
|---|---|
| `standard_transform_to_relative(transform)` | Converts 3x4 or 4x4 standard transforms to relative affine form used by Simplicits DOFs. |
| `create_projection_matrix(num_dofs, list_of_kin_dofs)` | Builds projection matrices for kinematic DOF removal. |
| `hess_reduction(dense_Ja, block_wise_H, dense_Jb=None)` | Dense Hessian block reduction helper. |
| `finite_diff_jac(fcn, x, eps=1e-7)` | Finite-difference Jacobian for small tests/debugging. |
| Warp sparse conversion helpers | Internal sparse matrix assembly/conversion; use for diagnostics, not as a public data-conversion API. |

## Experimental Newton integration

The Newton bridge is experimental and import-gated by the optional `newton`
package. Treat APIs as version-sensitive. Prefer bounded planning unless the
user explicitly requests and the probe confirms `newton`, Warp, and CUDA.

### `SimplicitsModelBuilder(up_axis=Axis.Z, gravity=-9.81)`

Extends Newton's builder. It defers Simplicits scene setup until `finalize`.

| Method | Use | Notes |
|---|---|---|
| `add_simplicits_object(sim_object, num_qp=None, init_transform=None, is_kinematic=False, renderable_pts=None)` | Add a Simplicits soft body to a combined Newton model | `SimplicitsObject` requires `num_qp`; baked points cannot also take `renderable_pts`. |
| `add_simplicits_collisions(...)` | Enable deferred soft-body self/inter-object collision | Applied during `finalize`. |
| `add_simplicits_object_boundary_condition(obj_idx, name, fcn, bdry_penalty=10000.0, pinned_x=None)` | Queue a boundary condition | Applied during `finalize`. |
| `finalize(device="cuda", requires_grad=False, **kwargs)` | Build `SimplicitsModel` | `requires_grad=True` warns; Simplicits is not differentiable yet. |

During `finalize`, Simplicits particles are added to Newton particle arrays;
Simplicits owns their dynamics, while Newton collision/contact systems can see
their current positions.

### `SimplicitsModel`

Extends Newton's `Model` and owns a `simplicits_scene`.

- `state(requires_grad=None)` returns `SimplicitsState` with `sim_z`,
  `sim_z_dot`, and `sim_z_prev` initialized when the scene is ready.
- `sim_z_to_full(sim_z)` maps reduced Simplicits DOFs to full particle
  positions.
- `sim_z_dot_to_full(sim_z_dot)` maps reduced velocities to full particle
  velocities.

### `SimplicitsState`

Extends Newton's state with:

- `sim_z`: reduced Simplicits positions.
- `sim_z_dot`: reduced velocities.
- `sim_z_prev`: previous reduced positions.

### `SimplicitsSolver(model)`

Newton solver wrapper. `step(state_in, state_out, control, contacts, dt)` copies
state into `model.simplicits_scene`, updates optional Newton soft contacts,
runs `SimplicitsScene.run_sim_step()`, writes reduced DOFs back to `state_out`,
and updates only the Simplicits particle slice in Newton particle arrays.

## Native verification candidates for this area

For later verification planning:

- CPU-safe or mostly CPU-safe material utility tests cover `to_lame` and Torch
  reference elastic formulas.
- Scene setup, Simplicits training, Warp loss kernels, collision, and RKPM/FEM
  comparisons are CUDA/Warp-gated and can be expensive.
- Experimental Newton builder/model/solver/collision tests are optional
  dependency gated and should not be treated as required unless Newton coupling
  is in scope.
