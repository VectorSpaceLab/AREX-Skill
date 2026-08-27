# Training and prediction workflows

This reference assumes feature columns and model-input dictionaries are already valid. If feature names, dense widths, sparse vocabulary sizes, or sequence arrays are uncertain, first use [`../../feature-column-inputs/SKILL.md`](../../feature-column-inputs/SKILL.md).

## Minimal binary DeepFM workflow

```python
import torch
from deepctr_torch.inputs import SparseFeat, DenseFeat, get_feature_names
from deepctr_torch.models import DeepFM

fixlen_feature_columns = [
    SparseFeat("user_id", vocabulary_size=1000, embedding_dim=4),
    SparseFeat("item_id", vocabulary_size=500, embedding_dim=4),
    DenseFeat("price", 1),
]
linear_feature_columns = fixlen_feature_columns
dnn_feature_columns = fixlen_feature_columns
feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)

train_model_input = {name: train_df[name].values for name in feature_names}
valid_model_input = {name: valid_df[name].values for name in feature_names}

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = DeepFM(
    linear_feature_columns=linear_feature_columns,
    dnn_feature_columns=dnn_feature_columns,
    task="binary",
    device=device,
)
model.compile("adagrad", "binary_crossentropy", metrics=["binary_crossentropy", "auc"])
history = model.fit(
    train_model_input,
    train_df["label"].values,
    batch_size=256,
    epochs=10,
    verbose=2,
    validation_data=(valid_model_input, valid_df["label"].values),
)
pred = model.predict(valid_model_input, batch_size=256)
eval_result = model.evaluate(valid_model_input, valid_df["label"].values, batch_size=256)
```

Prediction shape is normally `(n_samples, 1)`. `evaluate` returns a dictionary for the compiled metrics. It does not add a separate loss entry unless that loss was also included as a metric.

## `compile` choices

Exact string values implemented by the base model:

- Optimizers: `sgd`, `adam`, `adagrad`, `rmsprop`
- Losses: `binary_crossentropy`, `mse`, `mae`
- Metrics: `binary_crossentropy`, `logloss`, `auc`, `mse`, `accuracy`, `acc`

You may also pass a PyTorch optimizer instance instead of an optimizer string, and may pass callable loss functions/metrics if the call signatures match the base model's usage.

Recommended pairings:

| Task | Model constructor | Loss | Metrics |
|---|---|---|---|
| Binary classification | `task='binary'` | `binary_crossentropy` | `binary_crossentropy`/`logloss`, `auc`, optionally `accuracy`/`acc` |
| Regression | `task='regression'` | `mse` or `mae` | `mse`; compute MAE externally if needed |

Do not use `auc`, `accuracy`, or `binary_crossentropy` for regression targets.

## `fit`, `predict`, and `evaluate` inputs

- `x` can be a dictionary keyed by feature names, or a list ordered according to the model's internal feature index.
- Dictionary input is safer because the model extracts arrays by feature name.
- One-dimensional feature arrays are expanded to `(n_samples, 1)` internally.
- Single-task `y` may be either shape `(n_samples,)` or a column vector `(n_samples, 1)`. Column-vector binary targets are supported.
- `batch_size=None` defaults to `256`.
- `validation_data=(val_x, val_y)` overrides `validation_split`.
- `validation_split` slices the last fraction of arrays before training; for small datasets, prefer an explicit validation set with both classes.

Metric details:

- During training, metrics are computed per batch and averaged over steps.
- `predict` returns NumPy `float64` predictions.
- `evaluate` recomputes predictions with `predict` and flattens `y_true`/`y_pred` before metric calls.
- For final reports, it is often clearer to call sklearn metrics on `pred.reshape(-1)` after prediction.

## Device and GPU selection

```python
import torch

device = "cpu"
if torch.cuda.is_available():
    device = "cuda:0"

model = DeepFM(linear_feature_columns, dnn_feature_columns, task="binary", device=device)
```

For multiple GPUs:

```python
model = DeepFM(
    linear_feature_columns,
    dnn_feature_columns,
    task="binary",
    device="cuda:0",
    gpus=[0, 1],
)
```

Rules:

- `device` must be `"cpu"` or a concrete CUDA device such as `"cuda:0"`.
- If `gpus` is set, `gpus[0]` must match `device`; otherwise construction raises `ValueError` with the message `` `gpus[0]` should be the same gpu with `device` ``.
- In multi-GPU `fit`, DeepCTR-Torch wraps the model in `torch.nn.DataParallel` and multiplies the effective batch size by the number of GPUs.
- Keep CPU as the fallback path for small smoke tests and environments without a CUDA-capable PyTorch build.

## Callbacks in single-task flows

```python
from deepctr_torch.callbacks import EarlyStopping, ModelCheckpoint

callbacks = [
    EarlyStopping(
        monitor="val_binary_crossentropy",
        min_delta=0,
        patience=1,
        mode="min",
        restore_best_weights=True,
    ),
    ModelCheckpoint(
        filepath="checkpoints/deepfm-{epoch:02d}-{val_binary_crossentropy:.4f}.pt",
        monitor="val_binary_crossentropy",
        save_best_only=True,
        save_weights_only=True,
        mode="min",
    ),
]

history = model.fit(
    train_model_input,
    y_train,
    validation_data=(valid_model_input, y_valid),
    callbacks=callbacks,
    epochs=10,
)
```

Callback signatures:

- `EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto', baseline=None, restore_best_weights=False)`
- `ModelCheckpoint(filepath, monitor='val_loss', verbose=0, save_best_only=False, save_weights_only=False, mode='auto', period=1)`

Use monitor names that are present in the history logs. Examples: `val_binary_crossentropy`, `val_auc`, `val_mse`, `loss`. If a monitored value is missing, early stopping ignores it and model checkpoint may skip saving best-only checkpoints.

## Save and load

Prefer saving weights and reconstructing the same model class/feature columns:

```python
import torch

# Save.
torch.save(model.state_dict(), "deepfm_weights.pt")

# Load into a freshly constructed model with the same columns/task/device.
loaded = DeepFM(linear_feature_columns, dnn_feature_columns, task="binary", device=device)
loaded.compile("adagrad", "binary_crossentropy", metrics=["binary_crossentropy"])
loaded.load_state_dict(torch.load("deepfm_weights.pt", map_location=device))
```

Full-object save/load is supported by PyTorch but is less portable across code and dependency versions:

```python
torch.save(model, "deepfm_full_model.pt")
model = torch.load("deepfm_full_model.pt", map_location=device)
```

## No-linear and model-specific constructor cases

DeepFM supports an intentionally absent linear part:

```python
model = DeepFM([], dnn_feature_columns, use_fm=True, dnn_hidden_units=(32,), task="binary", device=device)
```

`PNN` has no linear-column argument:

```python
model = PNN(dnn_feature_columns, use_inner=True, use_outter=False, kernel_type="mat", task="binary", device=device)
```

`MLR` uses region/base/bias feature groups:

```python
model = MLR(
    region_feature_columns,
    base_feature_columns=base_feature_columns,
    bias_feature_columns=bias_feature_columns,
    region_num=4,
    task="binary",
    device=device,
)
```

For `MLR`, ensure the input dictionary contains every feature name in the union of region, base, and bias feature columns.

## Convert binary DeepFM to regression ratings

Starting binary model:

```python
model = DeepFM(linear_feature_columns, dnn_feature_columns, task="binary", device=device)
model.compile("adagrad", "binary_crossentropy", metrics=["binary_crossentropy", "auc"])
```

Regression conversion:

```python
model = DeepFM(linear_feature_columns, dnn_feature_columns, task="regression", device=device)
model.compile("adam", "mse", metrics=["mse"])
history = model.fit(train_model_input, train_df["rating"].values, batch_size=256, epochs=10)
pred = model.predict(test_model_input, batch_size=256).reshape(-1)
```

Checklist for the conversion:

1. Change `task='binary'` to `task='regression'`.
2. Replace `binary_crossentropy` with `mse` or `mae`.
3. Replace `auc`, `accuracy`, and `acc` with `mse` or external regression metrics.
4. Use the scalar rating/value target, not a click label.
5. Interpret predictions as unbounded numeric values, not probabilities.
6. If desired, clip predictions after inference for presentation; do not clip before loss computation unless the modeling goal requires it.

## Smoke helper

Run the bundled binary smoke helper from the generated skill subtree:

```bash
python sub-skills/single-task-modeling/scripts/deepfm_binary_smoke.py --help
python sub-skills/single-task-modeling/scripts/deepfm_binary_smoke.py --epochs 1
```

The helper uses inline tiny data, avoids original sample files, and defaults to a one-epoch run.
