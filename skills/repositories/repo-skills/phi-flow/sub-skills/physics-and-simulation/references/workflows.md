# Physics and Simulation Workflows

This reference is self-contained for direct simulation work using `phi.physics`. It assumes the package is installed and that fields / geometries are already represented with `CenteredGrid`, `StaggeredGrid`, `PointCloud`, `Field`, `Box`, `Sphere`, `Cuboid`, or `Mesh`.

## Import pattern

```python
from phi.flow import *
from phi import field, math
from phi.physics import advect, diffuse, fluid, wave, sph
from phiml.math import extrapolation, Solve, batch, channel, dual, instance, tensor, vec
```

`from phi.flow import *` provides the common field and geometry classes. Import `wave` and `sph` explicitly before using them.

## API quick map

| Need | API | Safe default | Important constraints |
| --- | --- | --- | --- |
| Robust grid advection | `advect.semi_lagrangian(field, velocity, dt)` | Stable first choice | More diffusive than MacCormack; samples velocity backwards from grid points. |
| Lower-diffusion grid advection | `advect.mac_cormack(field, velocity, dt, correction_strength=1.0)` | Use when overshoot clamping is acceptable | Can introduce sharper features; reduce `correction_strength` if ringing appears. |
| Point/particle advection | `advect.points(points, velocity, dt, integrator=advect.euler)` | `advect.finite_rk4` for sampled grid velocities | Use after grid velocity projection; run `fluid.boundary_push()` after obstacle/domain interactions. |
| Differential advection term | `advect.differential(u, velocity, order=2, implicit=None, upwind=True)` | `order=2` on grids, `order=1` for simple FVM | Returns `-u·∇u`, not an integrated next state. |
| Explicit diffusion | `diffuse.explicit(u, diffusivity, dt, substeps=1)` | Increase `substeps` until CFL warning disappears | Fast but conditionally stable. |
| Implicit diffusion | `diffuse.implicit(field, diffusivity, dt, solve=Solve('CG'))` | Use for large `dt` or viscosity | Reuse a `Solve` object if custom tolerance/x0 is needed. |
| Periodic exact diffusion | `diffuse.fourier(field, diffusivity, dt)` | Periodic scalar/vector grids | Requires periodic extrapolation and constant diffusivity. |
| Pressure projection | `fluid.make_incompressible(velocity, obstacles=(), solve=Solve(), active=None, order=2)` | Staggered velocity + `Solve(x0=pressure)` in loops | Obstacles are unsupported for `order > 2`; mesh velocities do not accept obstacle masks. |
| Wave leapfrog | `wave.step(u, u_prev, c=1., dt=1., source=None)` | Keep `(u, u_prev)` pair | Use small CFL; returns `(u_next, u)`. |
| Wave Euler | `wave.euler_step(u, v, c=1., dt=1., source=None)` | Use when initial velocity is known | Returns `(u_next, v_next)`. |
| SPH graph | `sph.neighbor_graph(nodes, kernel, desired_neighbors=None, compute='kernel,grad')` | `kernel='poly6'` for simple fluid examples | `nodes` must be `Geometry`; `domain` is required for periodic search. |

## Operator-split incompressible fluid

Use operator splitting for practical low-order fluid simulations: advect velocity, optionally diffuse it, then solve pressure to remove divergence.

```python
domain = dict(x=64, y=64, bounds=Box(x=1, y=1))
velocity = StaggeredGrid(0, 0, **domain)
pressure = None


def fluid_step(v, p, dt=1.0, viscosity=0.0, obstacles=()):
    v = advect.semi_lagrangian(v, v, dt)
    if viscosity:
        v = diffuse.explicit(v, viscosity, dt, substeps=4)
    solve = Solve(x0=p) if p is not None else Solve()
    v, p = fluid.make_incompressible(v, obstacles, solve)
    return v, p

velocity, pressure = fluid_step(velocity, pressure, dt=0.5, viscosity=0.01)
```

Validation signals:

```python
div = field.divergence(velocity)
math.assert_close(0, div.values, abs_tolerance=1e-4)
```

Prefer `StaggeredGrid` for velocity because it matches MAC-grid fluid pressure projection patterns. `CenteredGrid` is supported but may need more care around `wide_stencil`, boundary extrapolation, and divergence tolerances.

## Boundary and obstacle recipes

### Per-side grid boundary / extrapolation

Grid constructors accept a second positional `boundary` argument and also support `extrapolation=`. Avoid passing both for the same grid.

```python
lid_boundary = {'x': 0, 'y-': 0, 'y+': vec(x=1, y=0)}
velocity = StaggeredGrid(0, lid_boundary, x=50, y=32)
```

Useful extrapolation meanings:

- `extrapolation.PERIODIC`: opposite side is copied; required by `diffuse.fourier()`.
- `extrapolation.BOUNDARY` / `extrapolation.ZERO_GRADIENT`: Neumann-like closest-value behavior.
- numeric constants such as `0`: constant outside values, commonly used for no-slip velocity components.
- `extrapolation.combine_sides(x=..., y=(lower, upper))`: mix conditions by direction and side.
- `some_field.as_boundary()`: use a spatially varying field as a boundary value.

### Obstacles

Pass `Geometry` directly for stationary obstacles or wrap it in `Obstacle` when the obstacle moves or rotates.

```python
bar = Obstacle(Cuboid(vec(x=50, y=50), x=6, y=60), angular_velocity=0.05)
velocity, pressure = fluid.make_incompressible(velocity, bar, Solve(x0=pressure))
```

Obstacle geometries must live in the same vector space as the velocity field. For moving obstacles, call `obs.at(new_center)`, `obs.shifted(delta)`, or `obs.rotated(angle)` to update the geometry while preserving velocity metadata.

## Passive marker advection

Advect scalar smoke, temperature, dye, or masks with the projected velocity. Use MacCormack for a sharper marker field when small overshoots are acceptable.

```python
smoke = CenteredGrid(0, extrapolation.ZERO_GRADIENT, x=64, y=64, bounds=Box(x=1, y=1))
velocity = StaggeredGrid(0, 0, x=64, y=64, bounds=Box(x=1, y=1))

smoke = advect.mac_cormack(smoke, velocity, dt=1.0, correction_strength=0.75)
velocity = advect.semi_lagrangian(velocity, velocity, dt=1.0)
velocity, pressure = fluid.make_incompressible(velocity, solve=Solve(x0=None))
```

If MacCormack causes visible ringing or negative concentration in downstream checks, reduce `correction_strength` or return to `semi_lagrangian`.

## Diffusion choices

### Explicit diffusion

```python
temperature = diffuse.explicit(temperature, diffusivity=0.1, dt=0.25, substeps=8)
```

Use explicit diffusion for small `dt * diffusivity / dx²`. If a CFL warning appears, either increase `substeps`, reduce `dt` / diffusivity, or switch to `diffuse.implicit()`.

### Implicit diffusion

```python
temperature = diffuse.implicit(temperature, diffusivity=1.0, dt=1.0, solve=Solve('CG', 1e-5, 1e-5))
```

Use implicit diffusion for stiff diffusion or large time steps. For meshes, pass `correct_skew=False` unless you also provide a suitable gradient field.

### Fourier diffusion

```python
periodic_grid = CenteredGrid(Noise(), extrapolation.PERIODIC, x=64, y=64)
periodic_grid = diffuse.fourier(periodic_grid, diffusivity=0.05, dt=1.0)
```

Fourier diffusion is exact for periodic fields with constant diffusivity. It asserts when the extrapolation is not periodic.

## FLIP / PIC particle-grid coupling

The core loop is:

1. Scatter particle velocity to a `StaggeredGrid`.
2. Fill missing grid values with `field.finite_fill()`.
3. Build an occupied `CenteredGrid` mask.
4. Apply forces and project with `active=occupied`.
5. Update particles by FLIP delta or PIC replacement.
6. Advect particles and push them outside obstacles / inside the domain.

```python
def flip_step(particles: PointCloud, obstacles: list, bounds: Box, dt=0.05, gravity=vec(x=0, y=-9.81), **grid_resolution):
    template = StaggeredGrid(0, 0, bounds, **grid_resolution)
    grid_v = prev_grid_v = field.finite_fill(
        resample(particles, template, scatter=True, outside_handling='clamp')
    )
    occupied = resample(
        field.mask(particles),
        CenteredGrid(0, grid_v.extrapolation.spatial_gradient(), grid_v.bounds, grid_v.resolution),
        scatter=True,
        outside_handling='clamp',
    )
    grid_v, pressure = fluid.make_incompressible(grid_v + gravity * dt, obstacles, active=occupied)

    # FLIP update. For PIC, replace this with: particles = resample(grid_v, to=particles)
    particles += resample(grid_v - prev_grid_v, to=particles)

    if obstacles:
        valid_region = ~union(obstacles)
        sample_velocity = grid_v * field.mask(valid_region)
    else:
        sample_velocity = grid_v
    particles = advect.points(particles, sample_velocity, dt, advect.finite_rk4)
    particles = fluid.boundary_push(particles, list(obstacles) + [~bounds], separation=0.5)
    return particles, pressure
```

Use small `dt` and low resolution first. Boundary push is not optional when particles can cross a solid or leave `bounds` during advection.

## Wave equation stepping

Use `wave.step()` for leapfrog / Verlet time stepping when you store the previous displacement. Use `wave.euler_step()` when the time derivative `v = du/dt` is part of the state.

```python
u = CenteredGrid(
    lambda x: math.exp(-100 * math.squared_norm(x - 0.5)),
    extrapolation.ZERO_GRADIENT,
    x=32,
    y=32,
    bounds=Box(x=1, y=1),
)
u_prev = u
for _ in range(24):
    u, u_prev = wave.step(u, u_prev, c=1.0, dt=0.002)
```

Run the bundled smoke helper from this sub-skill directory:

```bash
python scripts/wave_smoke.py --resolution 32 --steps 24 --dt 0.002
```

Use `source=` for additive forcing, but make it a `Field` compatible with `u`. As a rule of thumb, keep `c * dt / dx` well below 1 during smoke runs.

## SPH kernel and neighbor workflow

SPH utilities only build neighborhoods and kernel values; you own the physical force model and integration.

```python
particles = PointCloud(Sphere(tensor([(0.25, 0.5), (0.5, 0.5), (0.75, 0.5)], instance('particles'), channel('vector')), radius=0.02))
domain = Box(x=1, y=1)
graph = sph.neighbor_graph(
    particles.geometry,
    kernel='poly6',
    desired_neighbors=30,
    compute='kernel,grad,laplace',
    domain=domain,
)
weights = graph.edges['kernel']
density_proxy = math.sum(weights, dual)
```

Supported kernel names are `quintic-spline`, `wendland-c2`, and `poly6`. Defaults for `desired_neighbors` are chosen per kernel. Specify `format='csr'`, `format='coo'`, or `format='dense'` when a downstream sparse operation requires a particular layout.

## Higher-order flow

Use differential PDE terms plus `fluid.incompressible_rk4()` when operator splitting is not accurate enough.

```python
def momentum_equation(v, viscosity=0.001):
    advection = advect.finite_difference(v, v, order=6)
    diffusion = diffuse.finite_difference(v, viscosity, order=6)
    return advection + diffusion

velocity = CenteredGrid(Noise(vector='x,y'), extrapolation.PERIODIC, x=64, y=64, bounds=Box(x=2 * math.PI, y=2 * math.PI))
velocity, pressure = fluid.make_incompressible(velocity, order=4)
velocity, pressure = fluid.incompressible_rk4(
    momentum_equation,
    velocity,
    pressure,
    dt=0.01,
    pressure_order=4,
    pressure_solve=Solve('CG', 1e-5, 1e-5),
)
```

Practical limits:

- Obstacles are supported only with `order <= 2` in `make_incompressible()`.
- Higher-order tests are tied to JAX coverage; CPU JAX is sufficient for correctness smoke checks, while CUDA is optional acceleration.
- Use `math.precision(64)` for strict value comparisons.
- Keep grids small until the solver and backend are known to be stable.

## Finite-volume mesh terms

For unstructured meshes, use `Field(mesh, values, boundary)` and direct differential terms. Boundary dictionary keys must match mesh boundary names.

```python
@jit_compile_linear
def momentum_eq(u, u_prev, dt, diffusivity=0.01):
    diffusion_term = dt * diffuse.differential(u, diffusivity, correct_skew=False)
    advection_term = dt * advect.differential(u, u_prev, order=1)
    return u + advection_term + diffusion_term
```

For implicit FVM steps, pass the function to `math.solve_linear()` and then project with `fluid.make_incompressible()` if the mesh field represents velocity. Use `correct_skew=False` unless a gradient correction has been prepared.

## Legacy `Domain` behavior

`phi.physics._boundaries.Domain` and convenience methods such as `scalar_grid()` / `staggered_grid()` still exist for legacy code but emit deprecation warnings. Prefer direct dictionaries and constructors:

```python
# Preferred modern pattern
domain = dict(x=16, y=16, bounds=Box(x=1, y=1), extrapolation=extrapolation.PERIODIC)
scalar = CenteredGrid(0, **domain)
velocity = StaggeredGrid(0, **domain)
```

When maintaining legacy snippets, `Domain(..., boundaries=...)` maps named slots like `scalar`, `vector`, `active`, and `accessible` to extrapolations. Do not introduce new code that depends on `Domain` unless the task is specifically a legacy migration or compatibility test.

## Native verification candidates for this area

The relevant native candidates are the physics tests for advection, diffusion, fluid projection, FLIP, SPH, higher-order flow, finite-volume mesh terms, and legacy boundaries, plus the bundled wave smoke helper. These candidates exercise the same API surfaces described here but should be run by the whole-skill verification phase, not while drafting this sub-skill.
