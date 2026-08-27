# Optional Dependencies and Backend Setup

Most supervised estimators in this sub-skill rely only on the normal tslearn/scikit-learn stack. Shapelets add a Keras backend gate.

## Dependency map

| Dependency | Enables | Notes |
| --- | --- | --- |
| `numpy`, `scipy`, `scikit-learn` | k-NN, SVM/SVR, early classification, MLP wrappers, sklearn model-selection utilities | These are part of the standard supervised workflow stack. |
| `keras` 3+ | `tslearn.shapelets.LearningShapelets` | Required before shapelet models can be imported and fitted. |
| `torch` | Preferred Keras backend for shapelet smoke checks in this environment | Set `KERAS_BACKEND=torch` before importing `keras` or `tslearn.shapelets`. |
| `tensorflow` or `jax` | Alternative Keras backends | Use only when installed and selected before import. |
| `matplotlib` | Plotting in upstream docs examples | Not needed by the bundled smoke helper. |

## Keras backend order

`LearningShapelets` depends on Keras and a backend. The backend must be selected before the first `keras` import in the process:

```python
import os
os.environ.setdefault("KERAS_BACKEND", "torch")

from tslearn.shapelets import LearningShapelets
```

Important rules:

1. Prefer the environment variable; do not rely on `~/.keras/keras.json` for this workflow.
2. If `KERAS_BACKEND` is unset, tslearn tries to auto-select the first installed backend among `torch`, `tensorflow`, and `jax`.
3. If `keras` has already been imported with the wrong backend, setting `KERAS_BACKEND` later is too late. Restart the Python process and import again.
4. A tiny torch-backed `LearningShapelets` fit was verified during construction, so the bundled smoke helper includes a shapelet mode instead of treating shapelets as unavailable.

## Shapelet smoke check

Run this from the sub-skill directory or from a project that can resolve the script path:

```bash
python scripts/supervised_smoke.py --mode shapelets
```

If it fails, use [troubleshooting.md](troubleshooting.md) before assuming the model code is wrong.

## Non-shapelet supervised paths

- `tslearn.neighbors` uses time-series distance computations and sklearn neighbor wrappers.
- `tslearn.svm` uses sklearn/libsvm SVC/SVR wrappers, with GAK precomputation for time-series kernels.
- `tslearn.early_classification` uses sklearn-compatible classifiers and tslearn clustering/neighbor utilities internally.
- `tslearn.neural_network` wraps sklearn MLPs and does not use Keras or torch.
