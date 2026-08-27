# Backend selection and dependency matrix

DeepXDE supports five backend names. Backend choice is an import-time decision: select it before `import deepxde as dde`.

This generated skill verified only the **PyTorch CPU** path during construction. All other backend rows below are distilled from DeepXDE installation, CI, and source behavior and should be checked in the target environment before use.

## Backend dependency matrix

| `DDE_BACKEND` value | Required backend packages | Construction status | Operational notes |
|---|---|---|---|
| `tensorflow.compat.v1` | `tensorflow>=2.7.0` exposing `tensorflow.compat.v1` | Optional, not verified here | Uses TensorFlow 1.x-style API inside TensorFlow 2.x and disables eager execution. DeepXDE sets `TF_FORCE_GPU_ALLOW_GROWTH=true` for TensorFlow backends. For TensorFlow 2.16+ / Keras 3 incompatibilities, install `tf-keras` and set `TF_USE_LEGACY_KERAS=1` before import when needed. |
| `tensorflow` | `tensorflow>=2.3.0` and `tensorflow-probability>=0.11.0` | Optional, not verified here | TensorFlow Probability is imported by the backend and is also used by TensorFlow L-BFGS utilities. DeepXDE sets `TF_FORCE_GPU_ALLOW_GROWTH=true`. For TensorFlow 2.16+ / Keras 3, use a TensorFlow Probability release compatible with the installed TensorFlow/Keras stack. |
| `pytorch` | `torch>=2.0.0` | **Verified with CPU** | Recommended default for this skill's safe examples. If CUDA is visible, DeepXDE's PyTorch backend sets CUDA as the default device; on macOS it attempts MPS and falls back if unusable. CPU-only operation remains valid. |
| `jax` | `jax`, plus `flax` and `optax` for neural-network/optimizer workflows | Optional, not verified here | JAX always uses XLA in DeepXDE configuration. Some platforms may not have all JAX wheels available. Validate import and device visibility before using. |
| `paddle` | `paddlepaddle>=2.6.0` | Optional, not verified here | If the installed Paddle build is compiled with CUDA, DeepXDE sets Paddle's default device to GPU. CPU Paddle is acceptable for CPU workflows if installed. |

## Backend selection priority

DeepXDE resolves the preferred backend in this order:

1. `DDE_BACKEND` environment variable.
   ```bash
   DDE_BACKEND=pytorch python script.py
   DDE_BACKEND=tensorflow.compat.v1 python script.py
   DDE_BACKEND=tensorflow python script.py
   DDE_BACKEND=jax python script.py
   DDE_BACKEND=paddle python script.py
   ```
2. Legacy `DDEBACKEND` environment variable, if present and `DDE_BACKEND` is absent.
3. Saved JSON config at `~/.deepxde/config.json`, for example:
   ```json
   {"backend": "pytorch"}
   ```
4. The helper command, which writes the same saved config:
   ```bash
   python -m deepxde.backend.set_default_backend pytorch
   ```
   Valid saved-backend options are `tensorflow.compat.v1`, `tensorflow`, `pytorch`, `jax`, and `paddle`.
5. Auto-detection, if no explicit environment variable or saved config exists. The source checks importability in this order: `tensorflow`, `tensorflow.compat.v1`, `pytorch`, `jax`, `paddle`. If none imports, DeepXDE can ask interactively about installing Paddle. Avoid this path in automated runs.

## Safe import patterns

### Shell-level selection

```bash
DDE_BACKEND=pytorch python train_or_diagnose.py
```

### Python-level selection

Set the environment variable before importing any DeepXDE module:

```python
import os
os.environ["DDE_BACKEND"] = "pytorch"

import deepxde as dde
print(dde.backend.backend_name)
```

### Persistent selection

Use the persistent config only when that is appropriate for the user account or container:

```bash
python -m deepxde.backend.set_default_backend pytorch
```

For reproducible scripts, prefer a process-local `DDE_BACKEND` over persistent config so the script is not affected by another user's saved backend.

## Diagnostic helper

Run the bundled script to validate importability and visible devices without creating models or requiring a GPU:

```bash
python scripts/check_backend.py --backend pytorch
python scripts/check_backend.py --backend pytorch --require-gpu
python scripts/check_backend.py --backend tensorflow --json
```

`--require-gpu` fails intentionally when no GPU device is visible; omit it for CPU-safe checks.
