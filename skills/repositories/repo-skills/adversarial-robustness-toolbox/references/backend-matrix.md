# Backend matrix

## Purpose

Use this reference when choosing packages or hardware before using ART workflows. The generated skill was validated against ART 1.20.1 with CPU-capable core workflows. GPU can accelerate PyTorch/TensorFlow attacks and training, but it is not required for the selected scope unless the user's own model or data workflow requires it.

## Package groups

| Group | Use when | Typical packages | Notes |
|---|---|---|---|
| Core scientific stack | Importing ART, sklearn estimators, NumPy preprocessors, many metrics | `adversarial-robustness-toolbox`, `numpy`, `scipy`, `scikit-learn`, `six`, `tqdm` | Start here for tabular, black-box, and many metric workflows. |
| PyTorch | `PyTorchClassifier`, PyTorch preprocessors, PyTorch evasion attacks, GREAT score, PyTorch certification | `torch`, `torchvision`; optionally `timm` for some model families | For CPU-only use, pass `device_type="cpu"` to ART PyTorch estimators/certifiers that expose it. |
| TensorFlow/Keras | `TensorFlowV2Classifier`, `KerasClassifier`, TensorFlow preprocessors, TensorFlow randomized smoothing | `tensorflow`, `keras` | No-CUDA startup messages are informational for CPU workflows. TensorFlowV2 `.fit()` needs a loss/optimizer or custom `train_step`. |
| Boosted trees | XGBoost/LightGBM/CatBoost classifier wrappers and black-box attacks | `xgboost`, `lightgbm`, `catboost` | Tree models usually do not provide loss gradients; choose black-box attacks or tree-specific verification. |
| GPy | Gaussian process classifier wrapper | `GPy` | Keep NumPy/SciPy compatibility in mind; avoid blindly upgrading NumPy if GPy is required. |
| Image helpers | JPEG, spatial/image preprocessing, physical image attacks | `opencv-python`, `kornia`, `Pillow`, `matplotlib` | Use only for image workflows; validate channel order (`NCHW` vs `NHWC`) before attacks. |
| Logging and optimization helpers | SummaryWriter, some metrics/certification helpers | `tensorboardX`, `numba`, `statsmodels`, `cma`, `sortedcontainers`, `multiprocess` | Install only when the selected workflow imports them. |

## Backend criticality

| Capability | Required backend for selected skill | CPU substitute | Verification stance |
|---|---|---|---|
| Importing ART and using sklearn/black-box wrappers | CPU Python stack | Full | Required. |
| PyTorch estimators and evasion attacks | PyTorch CPU or GPU | Full for tiny/small workflows | Required for PyTorch coverage; GPU is optional acceleration. |
| TensorFlowV2/Keras estimators | TensorFlow/Keras CPU or GPU | Full for tiny/small workflows | Required for TensorFlow/Keras coverage; GPU is optional acceleration. |
| Boosted-tree wrappers | XGBoost/LightGBM/CatBoost CPU packages | Full | Required only when boosted-tree workflows are used. |
| Certification and verification | Varies by class; tree verification and small smoothing checks are CPU-capable | Partial to full depending on certifier | Treat long Monte Carlo or GPU-scale certification as workload-specific, not proof required for this selected scope. |
| Speech/object detection/tracking/malware/GAN/generation | Specialized optional runtimes | None or partial | Out of selected runtime scope; do not promise runnable coverage without refresh. |

## Quick checks

From this skill directory:

```bash
python scripts/inspect_art_install.py --json
python sub-skills/estimators-and-models/scripts/smoke_sklearn_blackbox.py
python sub-skills/evasion-and-preprocessing/scripts/smoke_preprocessor_numpy.py
```

For framework-specific work, prefer the nearest sub-skill smoke script. These checks are tiny and synthetic; they do not download datasets or run original repository examples.

## Common backend decisions

- **User only has predictions:** use `BlackBoxClassifier` / `BlackBoxRegressor`; avoid gradient-only attacks and route to black-box attacks or metrics that accept predictions.
- **User has a PyTorch model on CPU:** use `PyTorchClassifier(..., device_type="cpu")`; validate `channels_first=True` and `input_shape`.
- **User has a TensorFlow/Keras model:** decide between `TensorFlowV2Classifier` and `KerasClassifier`; provide `loss_object` and optimizer/train step if fitting or gradients are needed.
- **User has boosted trees:** wrap with the matching tree wrapper, then prefer prediction-only attacks such as ZOO or tree-specific verification instead of PGD/FGM.
- **User asks for CUDA because TensorFlow printed no-CUDA logs:** first decide whether the workflow actually requires GPU. For selected ART workflows, CPU is usually valid; only install GPU packages when the user's model scale or dependency explicitly requires them.
