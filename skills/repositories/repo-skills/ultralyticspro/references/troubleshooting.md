# Troubleshooting

## Purpose

Read this for cross-cutting failures that affect both training and prediction.

## 1. `ModuleNotFoundError: ultralytics`

**Symptom**

- The wrapper scripts fail immediately on import.
- `scripts/check_ultralytics_env.py` cannot probe the package.

**Likely cause**

- The public `ultralytics` package is not installed in the current environment.

**Recovery**

- Install it with `python -m pip install ultralytics`.
- Re-run `python scripts/check_ultralytics_env.py --show-presets`.

## 2. `ImportError` from `torch` or `torchvision`

**Symptom**

- The package imports fail before any training or prediction starts.

**Likely cause**

- A compatible PyTorch stack is missing or mismatched with the current Python
  version or accelerator backend.

**Recovery**

- Install the PyTorch build that matches the target environment.
- If you need GPU training, use a CUDA-enabled torch wheel that matches the
  driver and CUDA runtime on the host.
- If you only need the wrappers to parse or dry-run, keep execution in dry-run
  mode and do not launch a real model run.

## 3. Package config path not found

**Symptom**

- Errors like `FileNotFoundError` for `cfg/models/...`.

**Likely cause**

- The wrapper was pointed at a path that is not present in the installed
  `ultralytics` build, or a custom local YAML was not supplied.

**Recovery**

- Prefer the bundled presets, which resolve the verified package paths.
- For `train-yolo12`, provide a local `yolo12.yaml` file or choose a different
  preset.

## 4. Weight or sample asset download on first run

**Symptom**

- The run pauses to fetch a `.pt` file or cached asset.

**Likely cause**

- The pretrained weight is not already cached in the environment.

**Recovery**

- Allow the first download, or pre-stage the weights before execution.
- If you only need to inspect the command, stay in dry-run mode.

## 5. Legacy Windows path separators

**Symptom**

- A source script path like `ultralytics\cfg\...` fails on a non-Windows
  system.

**Likely cause**

- The original example used a Windows-style string literal.

**Recovery**

- Use the bundled wrappers, which resolve package paths directly from the
  installed `ultralytics` package.
- If you must keep the original script, normalize the path before execution.

## 6. `device=0` fails or no CUDA device is visible

**Symptom**

- Training fails when a preset or override targets GPU 0.

**Likely cause**

- CUDA is unavailable in the active environment, or the requested device is not
  visible to PyTorch.

**Recovery**

- Override to `--device cpu` for a CPU run.
- Or install a CUDA-capable torch build and verify `torch.cuda.is_available()`.

## 7. Benign `pynvml` deprecation warning

**Symptom**

- A warning mentions `pynvml` or `nvidia-ml-py` during import.

**Likely cause**

- The installed PyTorch build or a transitive dependency is still using the old
  `pynvml` import path.

**Recovery**

- Usually none is required for the repo wrappers.
- If you want quieter GPU telemetry, install `nvidia-ml-py` in the environment
  that provides the Ultralytics runtime.
