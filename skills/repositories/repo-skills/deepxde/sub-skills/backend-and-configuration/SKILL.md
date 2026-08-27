---
name: backend-and-configuration
description: "Install and select DeepXDE tensor backends and configure dtype,
  autodiff, random seed, XLA, GPU, and parallel settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# DeepXDE backend and configuration

Use this sub-skill when the task is about choosing or diagnosing a DeepXDE tensor backend, installing backend-specific dependencies, or configuring `dde.config` settings such as dtype, autodiff mode, random seed, XLA, and parallel scaling.

This construction verified DeepXDE with the **PyTorch backend on CPU**. TensorFlow, JAX, PaddlePaddle, GPU, Horovod, and MPI paths are supported by DeepXDE but were not runtime-verified here; treat them as optional/alternative paths until checked in the target environment.

## Fast path

1. Select the backend **before importing DeepXDE**:
   ```bash
   DDE_BACKEND=pytorch python your_script.py
   ```
   or, inside Python before `import deepxde`:
   ```python
   import os
   os.environ.setdefault("DDE_BACKEND", "pytorch")
   import deepxde as dde
   ```
2. Run the diagnostic helper when imports or devices are uncertain:
   ```bash
   python scripts/check_backend.py --backend pytorch
   python scripts/check_backend.py --backend tensorflow --json
   ```
3. Apply configuration immediately after importing DeepXDE and before constructing data, networks, or models:
   ```python
   dde.config.set_default_float("float32")
   dde.config.set_random_seed(1234)
   dde.config.set_default_autodiff("reverse")
   ```

## Runtime references

- Backend dependencies and selection order: [references/backend-selection.md](references/backend-selection.md)
- Configuration API behavior: [references/configuration.md](references/configuration.md)
- Failure triage: [references/troubleshooting.md](references/troubleshooting.md)
- Safe diagnostic script: [scripts/check_backend.py](scripts/check_backend.py)

## Route out of this sub-skill

- PDE/ODE/IDE/FPDE geometry, boundary conditions, residuals, and gradients: [../pinn-problem-setup/SKILL.md](../pinn-problem-setup/SKILL.md)
- `Model.compile`, training loops, callbacks, checkpoints, metrics, and predictions: [../training-workflows/SKILL.md](../training-workflows/SKILL.md)
- DeepONet, MIONet, operator datasets, PI-DeepONet, or ZCS operator workflows: [../operator-learning/SKILL.md](../operator-learning/SKILL.md)

## Operating rules

- Do not rely on backend auto-detection in reproducible scripts. Set `DDE_BACKEND` explicitly or set the saved DeepXDE config.
- Backend selection is resolved during import. Changing `DDE_BACKEND` after `import deepxde` is too late for the current process.
- Prefer `pytorch` for CPU-safe examples in this generated skill unless the user explicitly requests another backend and the required package set is installed.
- Never claim GPU, Horovod, TensorFlow, JAX, or PaddlePaddle verification from this skill alone. Use the diagnostic script and environment-specific tests first.
