# Physics and Simulation Troubleshooting

Use this when a direct `phi.physics` workflow fails, diverges, produces NaNs, or behaves differently across backends.

## Import and API mismatches

**Symptom:** `ModuleNotFoundError: phiml` or imports work only from a checkout.

- Run in an environment where the package and its `phiml` dependency are installed.
- Do not rely on the source checkout being on `PYTHONPATH`; this generated skill is meant to work from an installed package.
- Import wave/SPH modules explicitly:

```python
from phi.physics import wave, sph
```

**Symptom:** constructor rejects `boundary` / `extrapolation`.

- Current grid constructors accept a second positional `boundary` and also accept `extrapolation=`. Use one style per constructor call.
- Many examples use `boundary` as a user-facing term because extrapolations fill the boundary-condition role.

## Advection issues

**Symptom:** marker/smoke becomes too blurry.

- Switch from `advect.semi_lagrangian()` to `advect.mac_cormack()`.
- If MacCormack overshoots or rings, lower `correction_strength` such as `0.5` to `0.9`.

**Symptom:** point clouds leave the domain or pass through obstacles.

- Use a projected grid velocity for particle advection.
- Mask obstacle regions before sampling velocity when needed.
- Always call `fluid.boundary_push(particles, obstacles + [~bounds], separation=...)` after particle advection when particles can cross solids or leave bounds.

**Symptom:** RK4 point advection samples NaNs near invalid grid cells.

- Prefer `advect.finite_rk4`, which falls back to Euler where sampled velocity values become non-finite.
- Use `field.finite_fill()` after particle-to-grid scatter before sampling from the grid.

## Diffusion issues

**Symptom:** `diffuse.explicit()` emits a CFL warning or grows instead of smoothing.

- Increase `substeps`.
- Reduce `dt` or `diffusivity`.
- Use `diffuse.implicit()` for large diffusion amounts.

**Symptom:** `diffuse.fourier()` asserts.

- Fourier diffusion requires a periodic grid: create the field with `extrapolation.PERIODIC`.
- Fourier diffusion assumes constant diffusivity. Use `explicit()` / `implicit()` for non-periodic fields or spatially varying diffusivity.

**Symptom:** spatially varying diffusivity fails.

- Spatially varying diffusivity support is limited to centered grids and second-order stencils.
- For mesh / FVM workflows, pass `correct_skew=False` unless a compatible gradient field is available.

## Pressure projection and incompressible flow

**Symptom:** divergence remains high after `fluid.make_incompressible()`.

- Verify the velocity field is finite before projection.
- Prefer a `StaggeredGrid` velocity for MAC-style fluids.
- Reuse pressure guesses in loops with `Solve(x0=pressure)`.
- Tighten solver tolerances only after confirming boundary/extrapolation setup:

```python
velocity, pressure = fluid.make_incompressible(
    velocity,
    obstacles,
    Solve('CG', 1e-5, 1e-5, x0=pressure),
)
```

- For closed or periodic all-active domains, the pressure solve has a rank-deficient constant mode; the API handles common cases, but custom solves may still need a rank-deficiency-aware `Solve` configuration.

**Symptom:** solve does not converge.

- Start with smaller grids and `order=2`.
- Use a fresh `Solve()` or a pressure `x0` with matching batch/spatial dimensions.
- If the field has NaNs in inactive cells, pass a correct `active` mask.
- For mesh solves, check boundary dictionary keys and values first; then try `Solve('scipy-direct')` when SciPy is available.

**Symptom:** obstacle errors mention vector dimensions or unsupported order.

- Obstacle geometries must use the same physical vector dimensions as the velocity field.
- Wrap moving/rotating solids as `Obstacle(geometry, velocity=..., angular_velocity=...)`.
- Do not use obstacles with `make_incompressible(..., order>2)`.
- Mesh velocity fields do not support obstacle masks; build obstacle behavior into the mesh and its boundary dictionary instead.

## FLIP / PIC failures

**Symptom:** particle-to-grid velocity contains holes or NaNs.

- Scatter to a `StaggeredGrid` template using `outside_handling='clamp'`.
- Immediately call `field.finite_fill()` on the scattered grid.
- Build `occupied` from `field.mask(particles)` and pass it as `active=occupied` to pressure projection.

**Symptom:** FLIP particles gain too much noise.

- Use smaller `dt`.
- Blend toward PIC by replacing some of the FLIP delta with sampled grid velocity.
- Keep `boundary_push()` separation modest, such as `0.5` grid cells, to avoid large corrective jumps.

**Symptom:** particles remain inside obstacle after push.

- Include both solids and inverted domain bounds in the push list: `[obstacle, ~bounds]`.
- Confirm the obstacle geometry has the same coordinate scale as the particle positions.

## Wave stepping failures

**Symptom:** wave amplitudes explode or become non-finite.

- Reduce `dt`, reduce wave speed `c`, or increase grid spacing. Keep `c * dt / dx` well below 1 for smoke checks.
- Start with `extrapolation.ZERO_GRADIENT` and a small Gaussian pulse before adding sources or moving obstacles.
- Run the bundled helper with safe defaults:

```bash
python scripts/wave_smoke.py --resolution 32 --steps 24 --dt 0.002
```

**Symptom:** `source=` causes shape or resampling errors.

- Make `source` a `Field` compatible with the current amplitude field `u`.
- Resample the source to `u` before passing it if it was constructed on different geometry.

## SPH neighbor and kernel issues

**Symptom:** `sph.neighbor_graph()` asserts about `nodes`.

- Pass a `Geometry` collection such as the `.geometry` of a `PointCloud`, not raw tensors.

**Symptom:** no neighbors or density is near zero.

- Increase `desired_neighbors` or particle radius/volume consistency.
- Confirm particles are within the `domain` used by periodic neighbor search.
- Use the built-in defaults first: omit `desired_neighbors` for `quintic-spline`, `wendland-c2`, or `poly6`.

**Symptom:** sparse format errors.

- Keep `format='sparse'` or select a supported concrete format such as `csr`, `coo`, `csc`, or `dense` based on downstream operations.
- For periodic search, pass `domain=Box(...)` and `periodic=True` or a vector-valued periodic mask.

**Symptom:** kernel derivatives fail finite-difference checks.

- Use double precision for derivative-sensitive checks: `with math.precision(64): ...`.
- Check that `types` only contains `kernel`, `grad`, and `laplace`.
- Supported kernels are `quintic-spline`, `wendland-c2`, and `poly6`.

## Higher-order and FVM issues

**Symptom:** higher-order flow fails with obstacles.

- Pressure projection with obstacles is restricted to explicit second-order stencils. Remove obstacles or use `order=2`.

**Symptom:** higher-order values differ across backends.

- Use JAX for the known higher-order path when available.
- Use `math.precision(64)` for tight comparisons.
- Keep `dt`, grid size, and solver tolerances conservative.

**Symptom:** FVM matrix/function checks mismatch.

- Build the `Field(mesh, values, boundary)` with boundary keys that match the mesh boundary names exactly.
- Use `advect.differential(..., order=1)` for simple FVM advection.
- Pass `correct_skew=False` unless a gradient correction has been prepared.
- Compare `A @ velocity.values + b` to `momentum_eq(...).values` when debugging `math.matrix_from_function()`.

## Legacy `Domain` warnings

**Symptom:** importing `phi.physics._boundaries.Domain` emits deprecation warnings.

- This is expected. Keep it only for legacy compatibility tasks.
- Prefer direct grid constructors and dictionaries:

```python
domain = dict(x=16, y=16, bounds=Box(x=1, y=1), extrapolation=extrapolation.PERIODIC)
scalar = CenteredGrid(0, **domain)
velocity = StaggeredGrid(0, **domain)
```

If a task specifically compares legacy behavior, isolate the warning expectation and avoid introducing `Domain` into new workflows.
