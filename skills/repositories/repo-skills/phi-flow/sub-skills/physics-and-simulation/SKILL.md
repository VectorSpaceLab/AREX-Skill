---
name: physics-and-simulation
description: "Route direct PDE, fluid, particle, and SPH simulation workflows
  built on phi.physics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Physics and Simulation

Use this sub-skill when the task is to run or modify direct simulation code with `phi.physics`: grid advection, diffusion, incompressible pressure projection, obstacles, particle/grid FLIP or PIC coupling, wave-equation stepping, SPH kernels, finite-volume mesh terms, higher-order fluid stepping, or legacy `Domain` / boundary behavior.

## Route here for

- **Advection:** `advect.semi_lagrangian()`, `advect.mac_cormack()`, `advect.advect()`, `advect.points()`, `advect.rk4()`, `advect.finite_rk4()`, and `advect.differential()` / `advect.finite_difference()`.
- **Diffusion:** `diffuse.explicit()`, `diffuse.implicit()`, `diffuse.fourier()`, `diffuse.differential()` / `diffuse.finite_difference()`.
- **Incompressible flow:** `fluid.make_incompressible()`, `fluid.Obstacle`, `fluid.apply_boundary_conditions()`, `fluid.boundary_push()`, and `fluid.incompressible_rk4()`.
- **Particles and SPH:** FLIP/PIC particle-grid transfer patterns, boundary push after point advection, `sph.neighbor_graph()`, `sph.evaluate_kernel()`, and SPH kernel forces.
- **Waves:** `wave.step()`, `wave.euler_step()`, `wave.differential()`, and the bundled deterministic wave smoke helper.
- **Boundaries:** modern grid `boundary` / `extrapolation` arguments, per-side extrapolations, `Obstacle` geometries, active masks, and deprecated `Domain` notes.
- **Higher-order and FVM:** direct PDE terms, orders 4/6 where supported, `fluid.incompressible_rk4()`, mesh `Field` boundary dictionaries, and finite-volume `diffuse.differential()` / `advect.differential()`.

Do **not** route optimization-through-gradients, plotting/UI, visualization-only notebooks, or maintainer-only topology-optimization demos here.

## Start with these imports

```python
from phi.flow import *
from phi import field, math
from phi.physics import advect, diffuse, fluid, wave, sph
from phiml.math import extrapolation, Solve, batch, channel, dual, instance, tensor, vec
```

Use the `phi.flow` import for common `CenteredGrid`, `StaggeredGrid`, `PointCloud`, `Box`, `Sphere`, `Cuboid`, `Obstacle`, `Noise`, `resample`, and math helpers. Import `wave` and `sph` explicitly; they are not part of the short fluid import trio.

## Most common decisions

1. **Grid fluid step:** create a `StaggeredGrid` velocity, optionally a marker `CenteredGrid`, then do advection -> diffusion -> projection. Prefer `Solve(x0=pressure)` in loops to reuse the pressure guess.
2. **Advection scheme:** use `semi_lagrangian` for robust defaults; use `mac_cormack` when numerical diffusion is the main issue and bounded correction is acceptable; use `advect.points(..., integrator=advect.finite_rk4)` for particle positions sampled from grids.
3. **Diffusion scheme:** use `explicit(..., substeps=N)` only when the diffusion CFL is safe; use `implicit()` for larger `dt` or viscosity; use `fourier()` only for periodic grids with constant diffusivity.
4. **Obstacle handling:** pass `Geometry` or `fluid.Obstacle` objects to `make_incompressible()`; use moving `Obstacle(..., velocity=..., angular_velocity=...)` to impose obstacle velocities. Higher-order pressure projection does not support obstacles.
5. **FLIP/PIC:** transfer particles to a grid, project with `active=occupied`, then update particles with either a FLIP delta (`particles += resample(grid_v - prev_grid_v, to=particles)`) or PIC replacement, advect points, and call `boundary_push()`.
6. **SPH:** build a particle `Geometry`, call `sph.neighbor_graph(nodes, kernel, ...)`, sum edge kernel values over `dual`, then integrate velocities and positions in your own step function.
7. **Waves:** use `wave.step(u, u_prev, c, dt)` for leapfrog state pairs or `wave.euler_step(u, v, c, dt)` when initial velocity is known. Keep `dt` small relative to grid spacing and wave speed.
8. **Legacy code:** replace deprecated `Domain(...)` helpers with direct constructor dictionaries when possible, e.g. `domain = dict(x=64, y=64, bounds=Box(x=1, y=1), extrapolation=extrapolation.PERIODIC)`.

## Verified signatures to rely on

- `advect.semi_lagrangian(field, velocity, dt, integrator=advect.euler)`
- `fluid.make_incompressible(velocity, obstacles=(), solve=Solve(), active=None, order=2, correct_skew=False, wide_stencil=None)`
- `wave.step(u, u_prev, c=1., dt=1., source=None)` and `wave.euler_step(u, v, c=1., dt=1., source=None)`
- `diffuse.explicit(u, diffusivity, dt, substeps=1, order=2, ...)`, `diffuse.implicit(field, diffusivity, dt, solve=Solve('CG'), ...)`, `diffuse.fourier(field, diffusivity, dt)`
- `sph.neighbor_graph(nodes, kernel, boundary=None, desired_neighbors=None, compute='kernel,grad', format='sparse', search_method='auto', domain=None, periodic=False)`

## Bundled references and helper

- Detailed recipes: [`references/workflows.md`](references/workflows.md)
- Failure handling: [`references/troubleshooting.md`](references/troubleshooting.md)
- Deterministic wave smoke: [`scripts/wave_smoke.py`](scripts/wave_smoke.py)

From this sub-skill directory, smoke-test wave stepping with:

```bash
python scripts/wave_smoke.py --resolution 32 --steps 24 --dt 0.002
```

The helper intentionally uses a small grid and far fewer steps than the source demo so it is safe as an installation/API smoke test rather than a benchmark.
