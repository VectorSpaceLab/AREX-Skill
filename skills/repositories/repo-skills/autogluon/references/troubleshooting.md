# Cross-Package Troubleshooting

## When To Read

Read this for AutoGluon install/import, optional dependency, CPU/GPU backend, version mismatch, or saved predictor failures that affect more than one subpackage. For workflow-specific fixes, continue to the owning sub-skill troubleshooting file.

## First Diagnostic

Run the bundled diagnostic in the user's target Python environment:

```bash
python scripts/check_autogluon_env.py --json
```

Use `--optional-backends` when the user asks about GPU, ONNX, TensorRT, OCR/PDF, Ray, or detection/export features.

## Install Or Import Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: autogluon.tabular` | Only namespace or wrong subpackage installed | Install `autogluon.tabular` or full `autogluon`; rerun import check. |
| `ModuleNotFoundError: autogluon.timeseries` | Time-series subpackage missing | Install `autogluon.timeseries`; expect Torch/forecasting dependencies. |
| `ModuleNotFoundError: autogluon.multimodal` | AutoMM subpackage missing | Install `autogluon.multimodal`; verify Torch/torchvision/transformers. |
| `pip check` reports dependency conflicts | Mixed versions from several installs | Recreate a clean environment or reinstall matching AutoGluon subpackages together. |
| Package supports Python range but compiled dependency fails | Dependency wheel not available for Python/OS | Use Python 3.10 or 3.11 for ML-heavy workflows unless the dependency stack is confirmed on newer Python. |
| Import works in one shell but not another | Different Python executable/environment | Ask the user to run `python -c "import sys; print(sys.executable)"` in both shells and install into the intended one. |

## CPU/GPU Backend Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| GPU host but `torch.cuda.is_available()` is false | CPU-only torch, missing driver passthrough, or incompatible CUDA wheel | Verify `nvidia-smi`, install a torch CUDA wheel compatible with the driver, or choose CPU-safe models. |
| `torchvision` import fails with missing ops or circular extension errors | Torch and torchvision wheels do not match CPU/CUDA build tags | Reinstall matching torch/torchvision wheels from the same index and version family. |
| TensorRT/ONNX export imports fail | Optional deployment stack missing or platform-specific | Keep training/prediction separate; install `onnx`, `onnxruntime`, or TensorRT only for export tasks. |
| Object detection backend fails before training | MMDetection/MMCV or CUDA ops missing | Validate data format first; install the detection backend only if the workflow truly needs detection training/inference. |
| Forecasting model tries to download a foundation model | Chronos/Toto or transformer model selected without local cache | Choose local/statistical models for offline smoke checks or provide a local checkpoint/cache. |

Do not install broad GPU packages unless the user explicitly needs GPU behavior. CPU importability and schema checks are enough for many planning and validation tasks.

## Saved Predictor Load Issues

AutoGluon predictors are pickle-backed artifacts. Load only trusted predictor directories.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Version mismatch warning/error | Predictor saved with a different AutoGluon version | Prefer matching the original AutoGluon version. Relax version checks only for trusted, non-production recovery. |
| Python version mismatch | Saved on a different Python minor version | Recreate the original Python version when possible; otherwise load with caution and run predictions on small samples. |
| Missing optional model package on load/predict | Predictor contains a model family not installed now | Install the missing model package or use a different saved model if available. |
| File not found inside predictor directory | Directory copied incompletely or deployment cleanup removed artifacts | Recopy the full predictor directory or regenerate with `standalone=True`/deployment-safe settings when available. |
| Untrusted predictor directory | Pickle execution risk | Do not load; ask for a trusted artifact source or recreate the model. |

Subpackage-specific load APIs:

- Tabular: `TabularPredictor.load(path, require_version_match=True, require_py_version_match=True, check_packages=False)`.
- Time series: `TimeSeriesPredictor.load(path, require_version_match=True)`.
- Multimodal: `MultiModalPredictor.load(path, resume=False, verbosity=3)`.

## Optional Dependency Triage

1. Identify the owning sub-skill and task family.
2. Run a read-only import/version check first.
3. Install the smallest missing package family that supports the task.
4. Avoid dev/test/docs/benchmark requirements unless the user is developing AutoGluon itself.
5. Avoid external dataset downloads or model downloads unless the user permits network access and storage.

## When To Stop And Ask

Ask before proceeding when the next step would install broad optional extras, mutate a user-provided environment, download large models/datasets, require credentials, require expensive GPU training, or load an untrusted saved predictor.
