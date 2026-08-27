# Optimization and Learning Troubleshooting

## Backend does not support the requested derivative

**Symptom:** `math.functional_gradient()` or `math.jacobian()` fails for a
backend that was expected to work.

**Likely cause:** the backend does not expose Jacobians in the current build, or
it is only partially installed.

**Recovery:** use `phi.detect_backends()` to inspect the available backends,
then install or switch to one that supports the derivative path you need.

## JIT compilation surprises

**Symptom:** `jit_compile()` or `jit_compile_linear()` fails under JAX, or a
function that used to work now traces incorrectly.

**Likely cause:** the function has side effects, nested temporary callables, or
another tracing pattern that the backend cannot accept.

**Recovery:** make the function pure, remove nested temporary functions, and
retry without JIT first. If a tiny repeated call leaks trace records, clear the
function caches with `traces.clear()` and `recorded_mappings.clear()` on the
transformed function.

## PyTorch custom-gradient / SolveTape issues

**Symptom:** a PyTorch-backed differentiable workflow fails when nested custom
gradients or implicit solves are traced.

**Likely cause:** the workflow combines operations that PyTorch cannot trace
through in the current mode.

**Recovery:** simplify the function, avoid nested custom-gradient wrappers, and
keep `SolveTape` out of the traced path.

## Gradient descent does not converge

**Symptom:** the loss stays flat or the learned value diverges.

**Likely cause:** the step size is too large, the target is ill-conditioned, or
the loss is not sensitive enough to the parameter.

**Recovery:** reduce the update step, check the loss on a single forward pass,
and verify the loss function with a small finite-difference experiment first.

## Backward solve or linearization looks wrong

**Symptom:** a linearized solve and the direct call disagree.

**Likely cause:** the function being linearized is not actually linear in the
chosen argument, or a backend-specific approximation is in play.

**Recovery:** compare the direct expression, `solve_linear()` result, and any
matrix form on a tiny test case before scaling up.

## When to stop

Stop and hand the user back to the simulation or geometry sub-skills if the
problem is really about field construction, scene I/O, or raw PDE stepping
rather than the optimization wrapper itself.
