# DeepXDE backend and installation reference

## When to read

Read this when installing DeepXDE, choosing a tensor backend, or deciding whether a target environment can run a requested DeepXDE workflow.

## Package identity

- Distribution name: `DeepXDE`.
- Import name: `deepxde`.
- Python requirement from package metadata: `>=3.9`.
- Base dependencies from package metadata: `matplotlib`, `numpy`, `scikit-learn`, `scikit-optimize>=0.10.2`, `scipy`.
- DeepXDE itself does **not** vendor a tensor backend. Install at least one backend dependency stack.

## Backend dependency matrix

| DeepXDE backend value | Typical required packages | Notes |
| --- | --- | --- |
| `tensorflow.compat.v1` | `tensorflow>=2.7.0` | Uses `tensorflow.compat.v1` and disables eager execution. TensorFlow 2.16+/Keras 3 stacks may require `tf-keras` and `TF_USE_LEGACY_KERAS=1`. |
| `tensorflow` | `tensorflow>=2.3.0`, `tensorflow-probability>=0.11.0` | TensorFlow Probability must match the TensorFlow/Keras version. |
| `pytorch` | `torch>=2.0.0` | The verified construction path used PyTorch CPU. If CUDA is visible, DeepXDE's PyTorch backend may set the default device to CUDA. |
| `jax` | `jax`, `flax`, `optax` | JAX always uses XLA; not every DeepXDE feature has equal JAX support. |
| `paddle` | `paddlepaddle>=2.6.0` | Paddle covers many examples; use platform-appropriate CPU/GPU wheels. |

Use backend-specific package documentation for CUDA/ROCm/MPS wheels. A CPU wheel verifies CPU behavior only.

## Backend selection order

DeepXDE selects a backend during import. Highest priority first:

1. Process environment variable:
   ```bash
   DDE_BACKEND=pytorch python script.py
   ```
2. Persistent DeepXDE config file, written with:
   ```bash
   python -m deepxde.backend.set_default_backend pytorch
   ```
3. Auto-detection of installed backend packages.

For reproducible scripts, prefer process-local `DDE_BACKEND=...` and set it before `import deepxde`:

```python
import os
os.environ.setdefault("DDE_BACKEND", "pytorch")
import deepxde as dde
```

Changing `DDE_BACKEND` after importing `deepxde` is too late for the current Python process.

## Verified and unverified boundaries

This generated skill verified:

- `DDE_BACKEND=pytorch` import.
- PyTorch CPU import and device query.
- Simple `Interval`/`PDE`/`DirichletBC`/`FNN`/`Model` compile, one-step train, and predict smoke.

This generated skill does **not** claim verification for:

- TensorFlow, JAX, or Paddle runtime execution.
- GPU/CUDA/ROCm/MPS execution.
- Horovod/MPI parallel training.
- Long-running examples, notebooks, or benchmark-scale training.

Treat unsupported backends as optional until checked in the target environment with the bundled diagnostic and a workflow-specific smoke test.

## Practical install patterns

CPU-safe PyTorch path:

```bash
python -m pip install deepxde torch
DDE_BACKEND=pytorch python -c "import deepxde as dde; print(dde.backend.backend_name)"
```

TensorFlow 2.x path:

```bash
python -m pip install deepxde tensorflow tensorflow-probability
DDE_BACKEND=tensorflow python -c "import deepxde as dde; print(dde.backend.backend_name)"
```

JAX path:

```bash
python -m pip install deepxde jax flax optax
DDE_BACKEND=jax python -c "import deepxde as dde; print(dde.backend.backend_name)"
```

Paddle path:

```bash
python -m pip install deepxde paddlepaddle
DDE_BACKEND=paddle python -c "import deepxde as dde; print(dde.backend.backend_name)"
```

If a backend is not required by the task, switch to the verified PyTorch CPU route before debugging scientific-model code. If a backend is required, fix the backend stack first.

## Which sub-skill owns deeper detail

- Backend diagnostics and `dde.config` behavior: `sub-skills/backend-and-configuration/`.
- PINN geometry, residuals, and boundary/initial conditions: `sub-skills/pinn-problem-setup/`.
- `Model.compile`, `train`, callbacks, checkpoints, metrics, and plotting: `sub-skills/training-workflows/`.
- DeepONet/MIONet/PDEOperator data and network shapes: `sub-skills/operator-learning/`.
