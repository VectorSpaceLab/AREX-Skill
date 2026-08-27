# Backend and configuration troubleshooting

Start with the diagnostic helper:

```bash
python scripts/check_backend.py --backend pytorch
python scripts/check_backend.py --backend tensorflow --json
```

Remember: only PyTorch CPU was verified during construction. TensorFlow, JAX, PaddlePaddle, GPU, Horovod, and MPI paths are optional until validated in the target environment.

## Import selected the wrong backend

Symptoms:

- stderr says `Using backend: ...` but it is not the backend requested.
- Code changes `os.environ["DDE_BACKEND"]` after `import deepxde` and nothing changes.

Fix:

1. Set `DDE_BACKEND` before importing any DeepXDE module:
   ```python
   import os
   os.environ["DDE_BACKEND"] = "pytorch"
   import deepxde as dde
   ```
2. In shell scripts, prefer process-local selection:
   ```bash
   DDE_BACKEND=pytorch python script.py
   ```
3. Check whether persistent config is overriding expectations in another run:
   ```bash
   python -m deepxde.backend.set_default_backend pytorch
   ```
4. Avoid auto-detection in automated jobs; it can select the first importable backend rather than the intended one.

## Backend package is missing or broken

Symptoms:

- `Backend is set as BACKEND, but 'BACKEND' failed to import.`
- `ModuleNotFoundError` for `tensorflow`, `tensorflow_probability`, `torch`, `jax`, `flax`, `optax`, or `paddle`.

Fix by backend:

| Backend | Check | Typical action |
|---|---|---|
| `pytorch` | `python scripts/check_backend.py --backend pytorch` | Install a compatible `torch>=2.0.0`; CPU builds are sufficient for CPU examples. |
| `tensorflow.compat.v1` | `python scripts/check_backend.py --backend tensorflow.compat.v1` | Install `tensorflow>=2.7.0`; set `TF_USE_LEGACY_KERAS=1` with `tf-keras` if Keras 3 compatibility fails. |
| `tensorflow` | `python scripts/check_backend.py --backend tensorflow` | Install compatible `tensorflow` and `tensorflow-probability`; TensorFlow 2.16+/Keras 3 stacks need matching TensorFlow Probability guidance. |
| `jax` | `python scripts/check_backend.py --backend jax` | Install `jax`, `flax`, and `optax` for full DeepXDE neural-network workflows. |
| `paddle` | `python scripts/check_backend.py --backend paddle` | Install `paddlepaddle>=2.6.0` or a platform-appropriate Paddle build. |

If the user did not request a specific backend, fall back to the verified CPU-safe default:

```bash
DDE_BACKEND=pytorch python script.py
```

## TensorFlow / Keras / TensorFlow Probability failures

Common causes:

- TensorFlow 2.16+ with Keras 3 while a TensorFlow 1.x compatibility workflow expects Keras 2 behavior.
- TensorFlow Probability version does not match the installed TensorFlow/Keras stack.
- TensorFlow backend selected when only PyTorch was installed.

Actions:

1. If the task does not require TensorFlow, use the verified default:
   ```bash
   DDE_BACKEND=pytorch python script.py
   ```
2. For TensorFlow 1.x compatibility mode with Keras 3 issues, install `tf-keras` and set before import:
   ```bash
   TF_USE_LEGACY_KERAS=1 DDE_BACKEND=tensorflow.compat.v1 python script.py
   ```
3. For TensorFlow 2.x, install a TensorFlow Probability release compatible with the TensorFlow/Keras version, then rerun the diagnostic.

## XLA errors

Symptoms:

- `Backend PyTorch does not support XLA.`
- `Backend PaddlePaddle does not support XLA.`
- `Backend JAX always uses XLA.`
- TensorFlow 1.x backend says XLA can only be enabled on GPU.

Fix:

- PyTorch/Paddle CPU workflows: do not call `enable_xla_jit(True)`.
- JAX: do not call `disable_xla_jit()`.
- TensorFlow 1.x CPU: do not enable XLA manually.
- TensorFlow 2.x GPU performance issue: try `dde.config.disable_xla_jit()` before model setup; optional TensorFlow auto-clustering flags are environment-specific.

## GPU required but not visible

Symptoms:

- Diagnostic with `--require-gpu` fails.
- Backend reports zero GPUs.
- PyTorch CPU build is installed.

Fix:

1. Decide whether GPU is actually required. CPU is enough for the bundled smoke examples.
2. Install a GPU-enabled backend build and matching driver/runtime for the platform.
3. Re-run:
   ```bash
   python scripts/check_backend.py --backend pytorch --require-gpu
   ```
4. Do not claim GPU verification until the diagnostic and at least one task-level smoke test pass.

## PyTorch or Paddle unexpectedly uses GPU

DeepXDE's PyTorch backend sets CUDA as the default device when CUDA is available. Its Paddle backend sets GPU as the default device when Paddle is compiled with CUDA.

Actions:

- For CPU-only PyTorch runs, ensure the process does not expose CUDA devices before importing DeepXDE when that is required by the environment policy.
- For Paddle, use a CPU Paddle build or platform-specific device controls before import.
- Re-run the diagnostic and confirm device state before creating tensors or models.

## Horovod/MPI failure

Symptoms:

- `NotImplementedError: Parallel training via Horovod is only implemented in backend tensorflow.compat.v1`.
- MPI environment variables are present while using PyTorch, TensorFlow 2.x, JAX, or Paddle.

Fix:

- Use Horovod only with `DDE_BACKEND=tensorflow.compat.v1` and a properly installed `horovod` + `mpi4py` stack.
- Remove MPI launch/environment variables for non-Horovod workflows.
- Set `dde.config.set_parallel_scaling("weak")` or `"strong"` only in validated Horovod scripts.

## Configuration call raises `ValueError`

Map the error to the configuration API:

- `set_default_float("mixed")` on unsupported backend: use `float32` or switch to TensorFlow 2.x/PyTorch after validating dependencies.
- `set_default_autodiff(...)`: use only `"reverse"` or `"forward"`.
- `enable_xla_jit(...)`: respect backend-specific XLA restrictions.

## Route unrelated issues

- PDE construction, boundary conditions, residual signatures, or gradients: [../../pinn-problem-setup/SKILL.md](../../pinn-problem-setup/SKILL.md)
- Training loops, `Model.compile`, callbacks, checkpoints, metrics, or prediction: [../../training-workflows/SKILL.md](../../training-workflows/SKILL.md)
- DeepONet, MIONet, operator-learning data shapes, or ZCS workflows: [../../operator-learning/SKILL.md](../../operator-learning/SKILL.md)
