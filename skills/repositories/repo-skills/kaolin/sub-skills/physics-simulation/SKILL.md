---
name: physics-simulation
description: "Operate Kaolin Simplicits physics, material, and experimental
  Newton-coupling workflows without running expensive simulations by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kaolin physics simulation

Use this sub-skill for Kaolin physics tasks involving Simplicits soft bodies,
point-sampled material data, scene setup, Warp/CUDA backend checks, and
experimental Newton coupling. Keep it as an operating router: read the bundled
references before proposing code, and use the bundled probe before promising a
simulation can run.

## Read first

- [API reference](references/api-reference.md) for Simplicits objects, material
  tensors, scene methods, and experimental Newton classes.
- [Workflows](references/workflows.md) for bounded mesh, point-cloud, Gaussian,
  baked-object, scene, and Newton-coupling plans.
- [Troubleshooting](references/troubleshooting.md) for Warp/CUDA, shape/device,
  scene setup, collision, Newton, and long-running notebook failures.
- [Backend probe](scripts/physics_backend_probe.py) for safe import/device checks.

## Use when

- A task asks for `kaolin.physics`, `kaolin.physics.simplicits`,
  `PhysicsPoints`, `SimplicitsObject`, `SkinnedPhysicsPoints`,
  `SimplicitsScene`, Simplicits training/baking/simulation, elastic materials,
  gravity/floor/boundaries/collisions, or reduced-coordinate deformation.
- A user has mesh, point-cloud, Gaussian, or baked skinned-physics data and wants
  a bounded plan to create physics inputs, add objects to a scene, step the
  simulation, or query deformed/rendered points.
- A task mentions Newton coupling with rigid bodies, MPM, or articulated robots;
  treat that path as experimental and optional-dependency gated.
- A setup fails due to missing Warp/CUDA/Newton, invalid material tensor shapes,
  wrong `num_qp`/`renderable_pts` usage, or scene-force ordering.

## Route elsewhere

- General geometry loading, OBJ/PLY/USD/GLTF importer details, `SurfaceMesh`,
  `PointSamples`, or `GaussianSplatModel` container construction: route to
  `geometry-io-representations`.
- Sampling/conversions such as mesh or Gaussian point sampling, densification,
  packed/padded tensor utilities, SPC, metrics, quaternion math, or generic
  tensor transforms: route to `ops-metrics-conversions`.
- Output visualization, Timelapse logging, notebook widgets, Dash3D/web servers,
  or rendered result presentation: route to `visualization-workflows`.
- Camera/rasterization/lighting setup for rendered images: route to
  `rendering-cameras-lighting`.

## Operating rules

1. **Probe before running.** Simplicits scene stepping is Warp/CUDA-sensitive;
   run or request `python scripts/physics_backend_probe.py --json` before
   recommending a real simulation run. Do not treat CPU tensor construction as
   proof that scene stepping works.
2. **Separate input preparation from simulation.** Ask geometry/ops owners to
   produce point samples and optional renderable points; this sub-skill owns the
   physics tensors, Simplicits object creation, scene forces, stepping, and
   deformation queries.
3. **Prefer bounded plans.** For notebooks/tutorial-style requests, avoid long
   MLP/RKPM training or asset downloads by default. Offer rigid/small-sample or
   baked-object smoke plans first, then mark full training as expensive.
4. **Keep tensor contracts explicit.** `pts` and renderable points are `(N, 3)`;
   `yms`, `prs`, and `rhos` are scalar or `(N,)`; `appx_vol` is scalar-like;
   `skinning_weights` are `(N, H)`; `dwdx` is `(N, H, 3)`.
5. **Record backend gates.** Warp and CUDA are required for practical scene
   stepping; Newton coupling additionally requires a compatible `newton` package.
   Browser/Jupyter/USD output paths are optional and routed to other sub-skills.
6. **Use internal references only.** Do not depend on the original repository,
   notebooks, tests, or local checkout paths at runtime; this sub-skill is the
   operating context.

## Minimal decision flow

1. Identify the representation: already point-sampled, mesh-derived, Gaussian-
   derived, or baked `SkinnedPhysicsPoints`.
2. Confirm backend target: dry-plan only, CPU construction smoke, CUDA/Warp
   simulation, or experimental Newton coupling.
3. Build/validate `PhysicsPoints` or `SkinnedPhysicsPoints` using the API table.
4. Choose object construction: rigid, custom function, MLP training, RKPM basis,
   or pre-baked load.
5. Build `SimplicitsScene`, add objects with correct `num_qp` and renderable
   points, set forces/collisions, then step only when backend probes pass.
6. Query `get_object_deformed_pts` or `get_object_point_transforms`; route
   logging/USD/visualization to the visualization or geometry I/O sub-skills.
