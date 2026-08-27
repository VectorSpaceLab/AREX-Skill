# LimiXPredictor Workflows

All examples below use placeholder local paths. Replace `path/to/local/...` with the caller's own checkpoint and config files. Do not assume a model will be downloaded automatically: `LimiXPredictor` loads `model_path` during construction.

## Safe preflight before full inference

From a LimiX checkout or an environment where LimiX is importable, run the bundled smoke helper first:

```bash
python sub-skills/predictor-inference/scripts/predictor_smoke_template.py \
  --repo-root . \
  --config path/to/local/cls_default_noretrieval.json \
  --model-path path/to/local/LimiX-16M.ckpt
```

Without `--run-inference`, the helper validates imports, config shape, fixture shapes, and local path existence. It does not instantiate the predictor and does not download a model.

## Classification recipe

Use this for one local tabular classification problem. Choose a non-retrieval config for CPU; choose a retrieval config only when CUDA/GPU is available and desired.

```python
import numpy as np
import torch
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from inference.predictor import LimiXPredictor

model_path = "path/to/local/LimiX-16M.ckpt"
config_path = "path/to/local/cls_default_noretrieval.json"  # CPU-safe; use retrieval only on CUDA.

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.5, random_state=42, stratify=y
)

predictor = LimiXPredictor(
    device=device,
    model_path=model_path,
    inference_config=config_path,
    mix_precision=(device.type == "cuda"),
    seed=0,
)

proba = predictor.predict(X_train, y_train, X_test, task_type="Classification")
labels = np.argmax(proba, axis=1)

print("classes:", predictor.classes)
print("probability shape:", proba.shape)
print("accuracy:", accuracy_score(y_test, labels))
if proba.shape[1] == 2:
    print("roc_auc:", roc_auc_score(y_test, proba[:, 1]))
```

Key points:

- The output is already probabilities, not logits.
- The class-column order is available as `predictor.classes` after prediction.
- If `device` is CPU, the config must have retrieval disabled.

## Regression recipe

The predictor does not normalize regression targets for you. The native usage pattern normalizes `y_train`, predicts in normalized space, then denormalizes.

```python
import numpy as np
import torch
from functools import partial
from sklearn.datasets import fetch_california_housing
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

try:
    from sklearn.metrics import root_mean_squared_error as rmse_metric
except ImportError:
    from sklearn.metrics import mean_squared_error
    rmse_metric = partial(mean_squared_error, squared=False)

from inference.predictor import LimiXPredictor

model_path = "path/to/local/LimiX-16M.ckpt"
config_path = "path/to/local/reg_default_noretrieval.json"

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

housing = fetch_california_housing()
X_train, X_test, y_train, y_test = train_test_split(
    housing.data, housing.target, test_size=0.33, random_state=42
)

y_mean = y_train.mean()
y_std = y_train.std()
if y_std == 0:
    raise ValueError("Cannot z-normalize a constant regression target.")
y_train_z = (y_train - y_mean) / y_std
y_test_z = (y_test - y_mean) / y_std

predictor = LimiXPredictor(
    device=device,
    model_path=model_path,
    inference_config=config_path,
    mix_precision=(device.type == "cuda"),
    seed=0,
)

pred_z = predictor.predict(X_train, y_train_z, X_test, task_type="Regression")
pred_z_np = pred_z.detach().cpu().numpy()
pred = pred_z_np * y_std + y_mean

print("normalized RMSE:", rmse_metric(y_test_z, pred_z_np))
print("normalized R2:", r2_score(y_test_z, pred_z_np))
print("denormalized first predictions:", pred[:5])
```

Key points:

- Regression returns a torch tensor; convert it before NumPy/scikit-learn metrics.
- Keep the same target normalization for training labels and metric labels.
- Use a regression config; classification configs produce the wrong output semantics.

## Missing-value imputation recipe

Use MVI when the caller has a checkpoint that supports feature reconstruction, a local MVI config, and a test matrix with `np.nan` entries to reconstruct. The model table identifies MVI support for the 16M checkpoint; do not assume a smaller or custom checkpoint supports it.

```python
import numpy as np
import torch
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from inference.predictor import LimiXPredictor

model_path = "path/to/local/LimiX-16M.ckpt"
config_path = "path/to/local/reg_default_noretrieval_MVI.json"

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, _ = train_test_split(X, y, test_size=0.33, random_state=42, stratify=y)

# Keep feature scales bounded and consistent between train and test.
scaler = MinMaxScaler()
X_train = scaler.fit_transform(X_train).astype(np.float32)
X_test = scaler.transform(X_test).astype(np.float32)
y_train = np.asarray(y_train, dtype=np.float32)

rng = np.random.default_rng(42)
mask = rng.random(X_test.shape) < 0.30
X_test_masked = X_test.copy()
X_test_masked[mask] = np.nan

predictor = LimiXPredictor(
    device=device,
    model_path=model_path,
    inference_config=config_path,
    mask_prediction=True,
    mix_precision=(device.type == "cuda"),
    seed=0,
)

primary_pred, reconstructed_all = predictor.predict(
    X_train, y_train, X_test_masked, task_type="Regression"
)

reconstructed_test = reconstructed_all[-len(X_test):].astype(X_test.dtype, copy=False)
filled_test = X_test_masked.copy()
filled_test[mask] = reconstructed_test[mask]

print("primary prediction type:", type(primary_pred))
print("reconstructed test shape:", reconstructed_test.shape)
print("filled missing entries:", int(mask.sum()))
```

Key points:

- Pass the masked array to `x_test`; keep the unmasked original only for evaluation.
- The second tuple element reconstructs the concatenated train+test feature matrix; slice the final `len(x_test)` rows for test rows.
- For categorical columns, round reconstructed values to the nearest known category before scoring. The bundled `mvi_mask_fixture.py` demonstrates this evaluation pattern without loading LimiX.

## DDP flag handoff

`inference_with_DDP=True` is not a general-purpose local speed flag. It hands prediction to the distributed/NCCL inference path and should be enabled only when the parent workflow owns a CUDA distributed launch plan, such as a `torchrun`-managed multi-process job. Do not enable it on CPU, in no-GPU smoke tests, or just to process one tiny table.

For dataset-directory loops, result CSV generation, and command-line benchmark wrappers, use the sibling benchmark sub-skill instead of reimplementing those loops here.
