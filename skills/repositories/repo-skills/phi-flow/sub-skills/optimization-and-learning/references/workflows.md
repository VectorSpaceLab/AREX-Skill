# Optimization and Learning Workflows

## Public surface map

PhiFlow's optimization layer sits on top of `phi.math` and the field/physics
modules. The public functions most users reach for are:

- `math.functional_gradient()` / `field.functional_gradient()`
- `math.gradient()`
- `math.jacobian()`
- `math.jit_compile()` and `math.jit_compile_linear()`
- `math.solve_linear()` and `math.solve_nonlinear()`
- `math.minimize()`
- `field.l2_loss()`, `field.l1_loss()`, and `field.frequency_loss()`
- `math.matrix_from_function()` for linearized or matrix-based workflows

## Differentiable throw example

A small differentiable throw loop is the easiest end-to-end smoke test.
The basic pattern is:

```python
from phi.flow import *
from phi import math


def simulate_hit(pos, height, vel, angle, gravity=1.):
    vel_x, vel_y = math.cos(angle) * vel, math.sin(angle) * vel
    height = math.maximum(height, .5)
    hit_time = (vel_y + math.sqrt(vel_y**2 + 2 * gravity * height)) / gravity
    return pos + vel_x * hit_time


def loss_function(vel):
    return math.l2_loss(simulate_hit(10, 1, vel, 0) - 0)


gradient = math.functional_gradient(loss_function)
vel = 1.0
for _ in range(10):
    loss, (grad,) = gradient(vel)
    vel = vel - 0.2 * grad
```

Use `math.precision(64)` if you want a strict smoke check or a backend
comparison with very small tolerances.

## Differentiable simulation loop

For simulation-based learning, keep the physics step and the optimization step
separate:

1. Build a small state with `CenteredGrid`, `StaggeredGrid`, or `PointCloud`.
2. Advance the state with `advect`, `diffuse`, or `fluid`.
3. Compute a scalar loss with `field.l2_loss()` or a custom reduction.
4. Differentiate with `math.functional_gradient()` or `math.jacobian()`.
5. Update the learnable value with a small step size.

If the loop gets stiff, lower the step size, add solver reuse via `Solve(x0=...)`,
or reduce the spatial resolution before trying larger grids.

## JIT and solver notes

- JAX `jit_compile()` expects pure functions.
- Avoid nested custom-gradient patterns when a backend can no longer trace the
  combined graph.
- Use `math.jit_compile_linear()` for linearized functions that will be passed
  to `solve_linear()`.
- For mesh / FVM workflows, `math.matrix_from_function()` is often the easiest
  way to debug whether a linearized expression matches the direct call.

## Practical validation checks

- Does the loss decrease over several small steps?
- Does the backend support the requested derivative level?
- Does the optimized value match the expected target from the native tests?
- Does the loop stay finite when run with `math.precision(64)`?
