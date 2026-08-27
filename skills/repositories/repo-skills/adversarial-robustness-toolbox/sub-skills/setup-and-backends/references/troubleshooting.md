# Setup and backend troubleshooting

Start with the bundled diagnostic:

```bash
python scripts/inspect_art_install.py --json
```

Then map the first failing package to the user's intended workflow. Avoid broad upgrades until the failing backend is identified.

## `ModuleNotFoundError: No module named 'art'`

Likely causes:

- The user installed a different package name or installed ART into another Python environment.
- The active interpreter is not the one used for `pip install`.

Fix:

```bash
python -m pip show adversarial-robustness-toolbox
python -m pip install adversarial-robustness-toolbox
python - <<'PY'
import art
print(art.__version__)
PY
```

Remember: distribution name is `adversarial-robustness-toolbox`; import name is `art`.

## Optional dependency ImportError

ART imports its core package without installing every backend. Missing optional modules should be fixed with the smallest matching package group.

| Error mentions | Install or verify | Do not do this first |
|---|---|---|
| `torch`, `torchvision` | `python -m pip install "adversarial-robustness-toolbox[pytorch]"` or install a CPU/GPU torch wheel matching the host. | Do not install CUDA wheels on a CPU-only host unless the user requested GPU. |
| `tensorflow`, `keras`, `h5py` | `python -m pip install "adversarial-robustness-toolbox[tensorflow]"` and/or `"adversarial-robustness-toolbox[keras]"`. | Do not mix many TensorFlow/Keras major versions in one environment. |
| `xgboost` | `python -m pip install "adversarial-robustness-toolbox[xgboost]"`. | Do not install all tree packages unless the workflow needs them. |
| `lightgbm` | `python -m pip install "adversarial-robustness-toolbox[lightgbm]"`. | Do not replace scikit-learn to fix a LightGBM-only import without checking compatibility. |
| `catboost` | `python -m pip install "adversarial-robustness-toolbox[catboost]"`. | Do not install CatBoost for ordinary scikit-learn classifiers. |
| `GPy` | `python -m pip install "adversarial-robustness-toolbox[gpy]"`. | Do not upgrade NumPy to a major version that breaks the GPy/scientific stack. |
| `cv2`, `kornia`, `PIL` | Use `pytorch_image`, `tensorflow_image`, or install `opencv-python`, `kornia`, `Pillow` directly. | Do not assume these are needed for tabular attacks. |
| `tensorboardX` | `python -m pip install tensorboardX`. | Do not install TensorBoard logging unless using ART SummaryWriter output. |
| `numba`, `statsmodels`, `cma`, `sortedcontainers` | Install only the named helper package needed by the selected metric/attack. | Do not install the broad `all` extra as the first repair step. |

## NumPy, SciPy, TensorFlow, and `ml-dtypes` conflicts

Symptoms:

- `pip check` reports TensorFlow, `ml-dtypes`, NumPy, or SciPy incompatibilities.
- TensorFlow install silently upgrades NumPy and another package starts failing.
- GPy or SciPy extension imports fail after a resolver change.

Recovery pattern:

1. Use an isolated environment for ART plus the chosen framework stack.
2. Pick one TensorFlow/Keras version pair and keep their resolver constraints together.
3. For broad ART 1.20.x CPU workflows that include GPy and TensorFlow, a conservative scientific stack is NumPy 1.26.x plus compatible SciPy and `ml-dtypes` from the TensorFlow resolver.
4. Run:

   ```bash
   python -m pip check
   python scripts/inspect_art_install.py --include art,numpy,scipy,sklearn,tensorflow,keras,gpy --json
   ```

5. If the conflict remains, split TensorFlow and GPy workflows into separate environments rather than forcing incompatible package pins.

Do not treat a TensorFlow startup warning as a dependency conflict by itself. Only repair when imports, `pip check`, or a minimal user workflow fails.

## CPU-only PyTorch or no CUDA

Symptoms:

- `torch.cuda.is_available()` is `False`.
- A user created `PyTorchClassifier(...)` without specifying `device_type`.
- Errors mention CUDA libraries, no NVIDIA driver, or tensors on different devices.

Facts and fix:

- `PyTorchClassifier` defaults to `device_type="gpu"`.
- CPU users should pass `device_type="cpu"` explicitly:

  ```python
  classifier = PyTorchClassifier(
      model=model,
      loss=loss_fn,
      input_shape=input_shape,
      nb_classes=nb_classes,
      optimizer=optimizer,
      device_type="cpu",
  )
  ```

- Use the same explicit `device_type="cpu"` for PyTorch preprocessors and PyTorch certification estimators.
- If the user wants CPU only, install CPU torch/torchvision wheels and do not install CUDA packages.
- If the user expects GPU, first verify the host outside ART:

  ```python
  import torch
  print(torch.__version__)
  print(torch.cuda.is_available(), torch.cuda.device_count())
  ```

Only debug ART after PyTorch itself sees the expected devices.

## TensorFlow CPU/GPU startup messages

TensorFlow may print warnings about missing CUDA drivers, TensorRT, oneDNN optimizations, or CPU instruction sets. On a CPU workflow these are usually informational.

Treat as non-blocking when:

- `import tensorflow as tf` succeeds.
- `tf.config.list_physical_devices("GPU")` is empty because the user intends CPU.
- The ART TensorFlow estimator import succeeds.

Treat as blocking when:

- TensorFlow import raises an exception.
- `pip check` reports broken TensorFlow dependencies.
- The user expected a GPU and TensorFlow sees none.

Fix no-GPU surprises by deciding whether the user wants CPU or GPU:

- CPU: set `CUDA_VISIBLE_DEVICES=""` for deterministic checks and continue.
- GPU: install a TensorFlow build compatible with the host driver/CUDA stack, then verify TensorFlow before constructing ART estimators.

## Package version mismatch after installing extras

Symptoms:

- ART imported before installing extras but fails after adding TensorFlow, PyTorch, or tree packages.
- `pip check` reports conflicts.
- A backend imports but ART estimator construction fails due to old/new model package APIs.

Fix:

1. Record the intended workflow and required backend family.
2. Re-run `python -m pip check` and `python scripts/inspect_art_install.py --json`.
3. Remove unrelated extras from the environment if the resolver pulled a broad stack.
4. Pin the backend family deliberately. Example: keep PyTorch/torchvision versions from the same release family; keep TensorFlow/Keras versions that are designed to work together.
5. If two workflows require incompatible versions, split them into separate environments.

## Import succeeds but estimator construction fails

This sub-skill only proves install/import readiness. Route construction failures to `estimators-and-models` when errors mention:

- `clip_values`, `input_shape`, `nb_classes`, `channels_first`, or preprocessing tuples.
- Label format, one-hot labels vs class indices, logits vs probabilities.
- Missing `loss`, `optimizer`, `loss_object`, or `train_step`.
- White-box gradient methods on black-box wrappers.

## Quick decision tree

1. Does `import art` fail? Install or activate `adversarial-robustness-toolbox` in the current interpreter.
2. Does an optional backend import fail? Install only the matching extra/package.
3. Does PyTorch report no CUDA? Use `device_type="cpu"` unless the user needs GPU.
4. Does TensorFlow import but warn about CUDA? Ignore for CPU workflows; verify GPU only if required.
5. Does `pip check` fail after resolver changes? Pin or split environments before changing ART code.
6. Do imports pass but workflow code fails? Route to the workflow-specific sub-skill.
