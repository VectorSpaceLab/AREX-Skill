---
name: optimization-and-learning
description: "Routes PhiFlow gradient, Jacobian, solve, and inverse-design workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optimization and Learning

Use this sub-skill when a PhiFlow task depends on gradients, Jacobians,
backpropagation through simulation, linear or nonlinear solves, or other
optimization loops built on top of the field and physics APIs.

## Route here for

- `math.functional_gradient()`, `math.gradient()`, and `math.jacobian()`
- `math.jit_compile()` and `math.jit_compile_linear()`
- `math.solve_linear()`, `math.solve_nonlinear()`, and `math.minimize()`
- `field.functional_gradient()`, `field.l2_loss()`, `field.l1_loss()`, and
  `field.frequency_loss()`
- inverse problems such as the throw optimization example
- differentiable fluid / PDE loops that are optimized end-to-end
- linearized mesh or FVM workflows that use `math.matrix_from_function()`

## Do not route here

- plain simulation without optimization -> `physics-and-simulation`
- installation or backend setup -> `installation-and-backends`
- field / geometry / scene plumbing -> `core-data-and-geometry`
- plotting, display, or scalar log rendering -> `visualization-and-ui`

## Start with these imports

```python
from phi.flow import *
from phi import field, math
from phi.physics import advect, diffuse, fluid
from phiml.math import Solve, precision
from phiml.backend import Backend
```

## Most common decisions

1. **Choose the gradient API:** use `math.functional_gradient()` for the most
   common differentiable-simulation loops and `math.jacobian()` when you need a
   Jacobian for a backend that supports it.
2. **Pick a loss intentionally:** `field.l2_loss()` is the usual smoke-test
   loss; `field.frequency_loss()` is useful when the task is about regularizing
   spatial detail.
3. **Reuse solve guesses:** pass `Solve(x0=previous_solution)` in iterative
   loops so the pressure or state guess carries across steps.
4. **Respect backend limitations:** JAX requires pure functions inside
   `jit_compile()`. PyTorch and custom-gradient workflows have their own
   tracing constraints.
5. **Use precision carefully:** `math.precision(64)` is useful for gradient
   smoke checks and backend comparisons.

## Verified signatures to rely on

- `math.functional_gradient(f, wrt=None, get_output=True) -> Callable`
- `math.gradient(f, wrt=None, get_output=True) -> Callable`
- `math.jacobian(f, wrt=None, get_output=True) -> Callable`
- `math.jit_compile(f=None, auxiliary_args='', forget_traces=None)`
- `math.jit_compile_linear(f=None, auxiliary_args=None, forget_traces=None)`
- `math.solve_linear(f, y, solve, *f_args, grad_for_f=False, f_kwargs=None, **f_kwargs_)`
- `math.solve_nonlinear(f, y, solve)`
- `math.minimize(f, solve)`
- `field.functional_gradient(f, wrt=None, get_output=True)`

## Bundled references and helper

- Detailed workflows: [`references/workflows.md`](references/workflows.md)
- Failure handling: [`references/troubleshooting.md`](references/troubleshooting.md)
- Throw gradient smoke: [`scripts/throw_gradient_descent.py`](scripts/throw_gradient_descent.py)

From this sub-skill directory, run the smoke helper when you need to verify the
core gradient path:

```bash
python scripts/throw_gradient_descent.py --iterations 10 --step-size 0.2
```

The helper exercises a tiny differentiable throw optimization loop across the
installed backends that support Jacobians.
