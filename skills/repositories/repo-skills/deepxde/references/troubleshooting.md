# DeepXDE troubleshooting router

## When to read

Read this when a DeepXDE task fails and the failure surface is not yet clear. Use the symptom to route to the nearest sub-skill reference or bundled diagnostic.

## First diagnostic steps

1. Confirm the backend is selected before import:
   ```bash
   DDE_BACKEND=pytorch python -c "import deepxde as dde; print(dde.backend.backend_name)"
   ```
2. Run the root smoke for the verified PyTorch CPU path:
   ```bash
   python scripts/smoke_deepxde.py --backend pytorch --train-steps 1
   ```
3. For backend-specific import/device checks, run:
   ```bash
   python sub-skills/backend-and-configuration/scripts/check_backend.py --backend pytorch
   ```

## Symptom router

| Symptom | Likely cause | Go to |
| --- | --- | --- |
| `ModuleNotFoundError` for `tensorflow`, `tensorflow_probability`, `torch`, `jax`, `flax`, `optax`, or `paddle` | Selected backend package stack is missing or broken | [backend troubleshooting](../sub-skills/backend-and-configuration/references/troubleshooting.md) |
| DeepXDE prints `Using backend: ...` but it is not the desired backend | `DDE_BACKEND` was not set before import, or persistent config selected another backend | [backend selection](../sub-skills/backend-and-configuration/references/backend-selection.md) |
| Keras 3 / TensorFlow Probability compatibility errors | TensorFlow, Keras, and TFP versions are not aligned | [backend troubleshooting](../sub-skills/backend-and-configuration/references/troubleshooting.md) |
| GPU was expected but backend reports no GPU | CPU-only backend wheel, hidden device, driver/runtime mismatch, or unsupported GPU path | [backend troubleshooting](../sub-skills/backend-and-configuration/references/troubleshooting.md) |
| `pde(x, y)` cannot compute derivatives, gradients are `None`, or tensor operations fail | Residual uses NumPy/Python operations instead of backend tensor operations, or the derivative component/index is wrong | [PINN troubleshooting](../sub-skills/pinn-problem-setup/references/troubleshooting.md) |
| Boundary or point-set losses have shape/component errors | BC/IC component index, target shape, or point array shape is inconsistent | [PINN API reference](../sub-skills/pinn-problem-setup/references/api-reference.md) |
| Training is slow, unstable, or produces large/unbalanced losses | Sampling, optimizer, loss weights, network capacity, scaling, or residual formulation needs adjustment | [training troubleshooting](../sub-skills/training-workflows/references/troubleshooting.md) and [PINN workflows](../sub-skills/pinn-problem-setup/references/pinn-workflows.md) |
| `batch_size` is ignored or fails for PDE data | PDE/TimePDE point resampling uses callbacks instead of ordinary mini-batching | [training lifecycle](../sub-skills/training-workflows/references/model-lifecycle.md) |
| Checkpoint restore fails across devices/backends | Backend-specific checkpoint protocol or `device` argument mismatch | [training troubleshooting](../sub-skills/training-workflows/references/troubleshooting.md) |
| Plotting blocks, opens windows, or fails in headless jobs | Interactive Matplotlib backend or `dde.saveplot(..., isplot=True)` in a non-GUI environment | [training troubleshooting](../sub-skills/training-workflows/references/troubleshooting.md) |
| DeepONet/MIONet label shapes do not match branch/trunk inputs | Confused `Triple` vs `TripleCartesianProd`, wrong Cartesian-product label matrix, or incompatible output strategy | [operator troubleshooting](../sub-skills/operator-learning/references/troubleshooting.md) |
| PI-DeepONet auxiliary variables or ZCS derivatives fail | PDEOperator/PDEOperatorCartesianProd input shape, backend support, or ZCS class mismatch | [operator workflows](../sub-skills/operator-learning/references/operator-workflows.md) |

## Safety boundaries

- The bundled smoke scripts are intentionally tiny and CPU-safe. Passing them means the installed package and selected backend can run minimal workflows, not that a scientific model is accurate.
- Do not run long demos, notebooks, GPU/Horovod jobs, or dataset-download workflows as diagnostics unless the user approves the cost and the target environment has the required dependencies.
- If a task explicitly requires TensorFlow, JAX, Paddle, GPU, or Horovod, verify that backend in the target environment before making workflow claims.
- If the package or source checkout has changed since [repo provenance](repo-provenance.md), refresh this skill before treating stale API details as authoritative.
