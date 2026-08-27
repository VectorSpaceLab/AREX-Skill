# Setup and Cross-Cutting Troubleshooting

## Purpose

Read this when AutoKeras install, import, Keras backend, optional accelerator, or general runtime behavior is the blocker before a workflow-specific sub-skill can be used.

## Installation pattern

AutoKeras package metadata declares distribution `autokeras`, Python `>=3.8`, and runtime dependencies on `packaging`, `keras-tuner>=1.4.0`, `keras>=3.0.0`, and `dm-tree`. Keras 3 also needs a backend framework such as PyTorch, TensorFlow, or JAX.

```bash
python -m pip install autokeras
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
KERAS_BACKEND=torch python -c "import keras, autokeras as ak; print(ak.__version__, keras.backend.backend())"
```

If the user already standardized on TensorFlow or JAX, use the corresponding Keras 3 backend setup instead and set `KERAS_BACKEND` before importing Keras.

## Environment check helper

From the root of this generated skill, run:

```bash
python scripts/check_autokeras_env.py --backend torch
python scripts/check_autokeras_env.py --backend torch --show-signatures
```

The helper reports AutoKeras/Keras/backend versions, public API availability, and whether optional backend frameworks are importable. It does not train or download data.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: autokeras` | Package not installed in current Python | Install `autokeras` in the active environment; rerun the root check helper. |
| Keras imports the wrong backend | `KERAS_BACKEND` was unset or set after import | Set `KERAS_BACKEND` before the Python process starts. |
| Torch/TensorFlow/JAX import failure | Backend framework missing or incompatible | Install a Keras 3 compatible backend for the platform. |
| Search is very slow | Default `max_trials=100`, large data, heavy image/text blocks | Start with `max_trials=1`, `epochs=1`, small data, and batch size 2-8. |
| GPU not used | CPU backend package installed or backend not configured for GPU | Verify the backend framework's own GPU check; AutoKeras APIs are not a GPU proof by themselves. |
| External dataset download hangs | Original docs/examples fetch public datasets | Use bundled synthetic scripts or user-provided local data. |

## Optional GPU notes

This skill was scoped around CPU-verifiable package behavior. GPU acceleration can be useful for real AutoML searches, but it is a backend/framework concern:

1. Install a GPU-capable backend wheel matching the user's hardware and driver.
2. Verify the backend framework's own GPU check, such as `torch.cuda.is_available()` for PyTorch.
3. Run a tiny AutoKeras smoke after backend verification.
4. Do not use CPU import success as evidence that CUDA, ROCm, MPS, or another accelerator works.

## No CLI entry point

This source tree exposes Python APIs, not a documented AutoKeras command-line entry point. If a user asks for a CLI, provide Python scripts or notebooks around the public API rather than inventing an `autokeras` shell command.
