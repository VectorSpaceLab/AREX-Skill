# Training API and persistence

This reference covers cross-cutting DeepCTR-Torch training methods shared by single-task, DIN/DIEN, and multi-task models.

## Base model workflow

DeepCTR-Torch model classes inherit the same Keras-like methods:

```python
model.compile(optimizer, loss, metrics=None)
history = model.fit(model_input, y, batch_size=256, epochs=1, validation_split=0.0)
pred = model.predict(model_input, batch_size=256)
eval_result = model.evaluate(model_input, y, batch_size=256)
```

`model_input` may be a dictionary keyed by `get_feature_names(...)`; the model converts it internally to the feature order recorded at construction time.

## Supported compile strings

The source implementation maps only these built-in strings:

| Argument | Supported strings | Notes |
| --- | --- | --- |
| `optimizer` | `sgd`, `adam`, `adagrad`, `rmsprop` | You may also pass a PyTorch optimizer instance, such as `torch.optim.Adagrad(model.parameters(), lr=0.1)`. |
| `loss` | `binary_crossentropy`, `mse`, `mae` | Multi-task models accept a list of loss strings/functions, one per task. |
| `metrics` | `binary_crossentropy`, `logloss`, `auc`, `mse`, `accuracy`, `acc` | `auc` uses `sklearn.metrics.roc_auc_score` and requires both classes in the evaluated target slice. |

Unknown strings raise `NotImplementedError`.

## Fit inputs and target shapes

| Workflow | `x` / `model_input` | `y` |
| --- | --- | --- |
| Single-task binary/regression | dict of arrays keyed by feature names, or ordered list of arrays | shape `(n_samples,)` or `(n_samples, 1)` |
| DIN/DIEN | dict includes target sparse fields, `hist_*` arrays, and length/negative-history arrays when required | shape `(n_samples,)` or `(n_samples, 1)` |
| Multi-task | shared dict of input feature arrays | shape `(n_samples, num_tasks)` in `task_names` order |

All arrays must have the same first dimension. A one-dimensional feature array is expanded to `(n_samples, 1)` internally; dense vector features still need explicit width `(n_samples, dimension)`.

## Validation and metrics

- `validation_split` takes the last fraction of samples after any user-level train/test split. For tiny data, set `validation_split=0.0` unless you know each split has both classes.
- `validation_data` can be `(x_val, y_val)` or `(x_val, y_val, sample_weight)`.
- `History.history` stores `loss`, metric names, and `val_*` metric names when validation is active.
- Multi-task metrics are flattened by the base metric helper. For production reporting, compute per-task metrics outside the model using each prediction column.

## Device and GPU rules

Every model constructor accepts `device='cpu'` by default and most accept `gpus=None`.

```python
import torch

device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
model = DeepFM(linear_feature_columns, dnn_feature_columns, device=device)
```

For DataParallel:

```python
model = DeepFM(..., device='cuda:0', gpus=[0, 1])
```

`gpus[0]` must match the CUDA device string; otherwise the base model raises a `ValueError`. Do not treat a CPU import as evidence that a CUDA environment works. Run a torch CUDA smoke before choosing CUDA.

## Callbacks

DeepCTR-Torch includes simple callback classes in `deepctr_torch.callbacks`:

```python
from deepctr_torch.callbacks import EarlyStopping, ModelCheckpoint

es = EarlyStopping(monitor='val_binary_crossentropy', min_delta=0, patience=1, mode='min')
ckpt = ModelCheckpoint(filepath='model.ckpt', monitor='val_binary_crossentropy', save_best_only=True, mode='min')
history = model.fit(model_input, y, validation_split=0.2, callbacks=[es, ckpt])
```

Verified signatures:

- `EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto', baseline=None, restore_best_weights=False)`
- `ModelCheckpoint(filepath, monitor='val_loss', verbose=0, save_best_only=False, save_weights_only=False, mode='auto', period=1)`

Callback rules:

- The monitored key must exist in epoch logs. If you monitor `val_acc`, validation and `acc` metric must both be active.
- `mode='auto'` maximizes names containing `acc`, names ending in `auc`, or names starting with `fmeasure`; otherwise it minimizes.
- `ModelCheckpoint(save_weights_only=True)` writes `state_dict`; otherwise it pickles the full model object.

## Saving and loading

Weights-only pattern:

```python
import torch

model = DeepFM(linear_feature_columns, dnn_feature_columns)
# train...
torch.save(model.state_dict(), 'deepfm_weights.pt')
model.load_state_dict(torch.load('deepfm_weights.pt', map_location='cpu'))
```

Full-model pattern:

```python
torch.save(model, 'deepfm_model.pt')
model = torch.load('deepfm_model.pt', map_location='cpu')
```

Prefer weights-only plus reconstructed feature columns when portability matters. Full-model pickle files depend on Python/package compatibility.

## Bundled smoke helpers

- `sub-skills/single-task-modeling/scripts/deepfm_binary_smoke.py`
- `sub-skills/sequence-and-interest-models/scripts/din_sequence_smoke.py`
- `sub-skills/sequence-and-interest-models/scripts/varlen_feature_smoke.py`
- `sub-skills/multitask-modeling/scripts/mmoe_multitask_smoke.py`

Use these helpers for environment sanity checks and small workflow patterns. They use inline data and do not read external sample files.
