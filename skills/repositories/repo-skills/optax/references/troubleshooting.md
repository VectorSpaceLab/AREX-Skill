# Cross-Cutting Troubleshooting

Use this reference when a request fails before the actual Optax workflow starts or when the problem looks like install/import drift, backend mismatch, or a broad API misuse.

## Import or install fails

- If `import optax` fails with `ModuleNotFoundError: No module named 'jax'`, install a compatible `jax` and `jaxlib` pair first.
- If the package imports from one environment but not another, check that the shell is pointing at the intended Python environment before changing code.
- For a quick check, run the bundled doctor script instead of relying on a long test suite.
- If you are using a checkout, install in an isolated environment; do not assume system packages are enough.

## Backend confusion

- Optax is a JAX library, so the actual backend is determined by the installed JAX runtime.
- A CPU-only JAX install is enough to prove importability and many tiny smoke checks.
- A CPU import does **not** prove accelerator-specific behaviour. If the user asks about GPU or other accelerator execution, verify that backend explicitly.
- If `jax.devices()` shows only CPU when the user expected otherwise, the environment is missing the accelerator-capable JAX build.

## Tree, shape, and update errors

- Gradient transformations expect parameter and gradient PyTrees with matching structure.
- `apply_updates` requires the updates tree to line up with the parameter tree.
- If a transform needs the current parameters as input, pass them to `update(...)` consistently and do not reuse state from a different pipeline.
- Shape or dtype errors are often caused by an upstream preprocessing mismatch rather than by the optimizer itself.

## Loss and schedule issues

- Loss functions usually assume logits or raw predictions; do not substitute probabilities unless the docstring says so.
- Integer-label and one-hot variants are not interchangeable.
- Schedule callables usually expect a step index; make sure the training loop increments it the same way the schedule expects.
- If learning-rate changes look wrong, inspect schedule composition before changing the optimizer math.

## Projection, assignment, and advanced helper issues

- Projection helpers assume a feasible set interpretation that matches the function name; check whether the helper is projecting onto a ball, simplex, orthant, or hyperplane.
- `hungarian_algorithm` expects the correct cost-matrix shape and should be treated as an assignment primitive, not as a generic tensor transform.
- Tree utilities can silently expose shape mismatches if the caller mixes parameter trees with auxiliary trees.

## Contrib and experimental caveats

- `optax.contrib` and `optax.experimental` are useful, but they are the most likely places for API drift or extra state requirements.
- If a contrib algorithm behaves differently from an example, compare against the current docs and the bundled provenance before assuming the old recipe is still valid.
- Prefer the smallest reproducible case that exercises the contrib helper you actually need.

## Heavy validation

- The repository’s `test.sh` script is broad: it creates a virtualenv, runs pre-commit, installs editable test/docs dependencies, runs linting, builds a wheel, type-checks with pytype, runs pytest, and builds Sphinx docs.
- Use `scripts/optax_skill_doctor.py` for quick environment validation before committing to heavier checks.
