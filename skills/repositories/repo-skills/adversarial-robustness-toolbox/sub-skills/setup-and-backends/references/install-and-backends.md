# ART install and backend matrix

This reference covers the setup surface for ART 1.20.x. Install the public distribution `adversarial-robustness-toolbox`; import the package as `art`.

## Baseline install

Use an isolated Python environment. ART metadata advertises Python 3.10, 3.11, and 3.12 classifiers; Python 3.10 is a conservative choice when combining TensorFlow, PyTorch, GPy, and boosted-tree packages.

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install adversarial-robustness-toolbox
```

Core runtime dependencies from package metadata are:

| Layer | Packages | Notes |
|---|---|---|
| ART package | `adversarial-robustness-toolbox` | Distribution name; import module is `art`. |
| Core numeric stack | `numpy>=1.18.0`, `scipy>=1.4.1`, `scikit-learn>=0.22.2` | Enough for many NumPy/scikit-learn estimators, metrics, preprocessing, and non-framework checks. |
| Utilities | `six`, `setuptools`, `tqdm` | Pulled by the base package. |

Minimal import check:

```bash
python - <<'PY'
import art
print("ART", art.__version__)
from art import attacks, defences, estimators, evaluations, metrics, preprocessing
print("core modules ok")
PY
```

## Optional backend install groups

Install only the backend family required by the user's task. Quoting extras avoids shell glob expansion.

| Need | Recommended install command | What it enables | Import smoke |
|---|---|---|---|
| scikit-learn / NumPy workflows | `python -m pip install adversarial-robustness-toolbox` | Core ART plus scikit-learn wrappers and many CPU metrics/preprocessors. | `import art, numpy, scipy, sklearn` |
| PyTorch classification/regression/certification | `python -m pip install "adversarial-robustness-toolbox[pytorch]"` | `torch`, `torchvision`, PyTorch ART estimators and PyTorch preprocessors. | `import torch; from art.estimators.classification import PyTorchClassifier` |
| PyTorch image helpers | `python -m pip install "adversarial-robustness-toolbox[pytorch_image]"` | PyTorch plus `kornia`, `Pillow`, `ffmpeg-python`, `opencv-python` for image/vision transforms. | `import torch, torchvision, kornia, cv2` |
| TensorFlow v2 | `python -m pip install "adversarial-robustness-toolbox[tensorflow]"` | `tensorflow`, `h5py`, TensorFlow v2 estimators and preprocessors. | `import tensorflow as tf; from art.estimators.classification import TensorFlowV2Classifier` |
| Keras wrapper | `python -m pip install "adversarial-robustness-toolbox[keras]"` | `keras`, `h5py`, Keras classifier/regressor wrappers. | `import keras; from art.estimators.classification import KerasClassifier` |
| TensorFlow image helpers | `python -m pip install "adversarial-robustness-toolbox[tensorflow_image]"` | TensorFlow plus `Pillow`, `ffmpeg-python`, `opencv-python`. | `import tensorflow, cv2` |
| XGBoost | `python -m pip install "adversarial-robustness-toolbox[xgboost]"` | ART XGBoost classifier wrapper and tree verification inputs. | `import xgboost; from art.estimators.classification import XGBoostClassifier` |
| LightGBM | `python -m pip install "adversarial-robustness-toolbox[lightgbm]"` | ART LightGBM classifier wrapper. | `import lightgbm; from art.estimators.classification import LightGBMClassifier` |
| CatBoost | `python -m pip install "adversarial-robustness-toolbox[catboost]"` | ART CatBoost classifier wrapper. | `import catboost; from art.estimators.classification import CatBoostARTClassifier` |
| GPy | `python -m pip install "adversarial-robustness-toolbox[gpy]"` | ART Gaussian-process classifier support. | `import GPy; from art.estimators.classification import GPyGaussianProcessClassifier` |
| SummaryWriter / TensorBoard output | `python -m pip install tensorboardX` | ART `SummaryWriterDefault` runtime dependency. | `import tensorboardX; from art.summary_writer import SummaryWriterDefault` |
| Non-framework helpers | Install exact packages as needed: `matplotlib Pillow statsmodels pandas numba cma sortedcontainers opencv-python` | Plotting, statistics, optional metrics, image processing, optimisation, and utility paths. | Import only the packages used by the chosen workflow. |

The `all` extra exists, but it is usually too broad for a stable research environment. Prefer targeted extras; only use `all` for disposable integration environments where large resolver changes are acceptable.

## CPU vs GPU selection

The selected operating scope is CPU-capable. GPU packages are optional acceleration, not a prerequisite for ordinary ART import, scikit-learn workflows, many PyTorch/TensorFlow toy checks, or most tabular metrics.

### PyTorch

- ART's `PyTorchClassifier` default constructor value is `device_type="gpu"`.
- CPU users should pass `device_type="cpu"` in `PyTorchClassifier`, PyTorch regressors, PyTorch preprocessing defences, and PyTorch certification estimators.
- For CPU-only PyTorch wheels, install the CPU wheel index or the platform's standard CPU wheel, then install ART extras if needed.
- Verify before debugging ART:

```python
import torch
print(torch.__version__)
print("cuda available", torch.cuda.is_available())
```

If `torch.cuda.is_available()` is `False`, choose `device_type="cpu"` and continue unless the user's workload explicitly requires CUDA.

### TensorFlow/Keras

- TensorFlow normally selects available devices itself; ART's TensorFlow v2 classifier does not use a `device_type` constructor argument.
- CPU-only TensorFlow startup logs about missing CUDA libraries are common on CPU hosts. Treat them as warnings unless import or execution fails.
- To force CPU in a diagnostic shell, hide GPUs before import:

```bash
CUDA_VISIBLE_DEVICES="" python - <<'PY'
import tensorflow as tf
print(tf.__version__)
print(tf.config.list_physical_devices("GPU"))
PY
```

### Boosted trees and GPy

XGBoost, LightGBM, CatBoost, and GPy are optional model-family packages. They do not come from the base ART install. Install them only when the user wraps those model types or runs tree-specific verification/certification workflows.

## Minimal ART object imports

Use these as import-only checks. Estimator construction belongs to `estimators-and-models`.

```python
import art
print(art.__version__)

from art.estimators.classification import (
    SklearnClassifier,
    BlackBoxClassifier,
    PyTorchClassifier,
    TensorFlowV2Classifier,
    KerasClassifier,
    XGBoostClassifier,
    LightGBMClassifier,
    CatBoostARTClassifier,
    GPyGaussianProcessClassifier,
)
from art.estimators.regression import ScikitlearnRegressor, PyTorchRegressor, KerasRegressor, BlackBoxRegressor
from art.summary_writer import SummaryWriterDefault
```

If one of these imports fails, first identify whether the failing class actually belongs to the current workflow. Do not install TensorFlow, PyTorch, or all boosted-tree packages just to satisfy an unrelated import.

## Bundled diagnostic helper

Run the setup diagnostic from this sub-skill directory or with an explicit path:

```bash
python scripts/inspect_art_install.py
python scripts/inspect_art_install.py --json
python scripts/inspect_art_install.py --include art,numpy,scipy,sklearn,torch,tensorflow
```

Interpretation:

- `status: ok` means the module imported and a version was found when available.
- `status: missing` means the package is not installed; install the targeted extra from the matrix.
- `status: error` means import found something but startup failed; use `references/troubleshooting.md` before upgrading unrelated packages.
- For PyTorch, compare `cuda_available` with the intended `device_type`.
- For TensorFlow, compare the reported GPU list with the user's actual hardware expectation.
