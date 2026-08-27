# Single-task API reference

This reference lists the constructor and training APIs needed for single-output DeepCTR-Torch binary classification and regression workflows.

## Single-task model constructors

Common tail parameters across most models include `l2_reg_linear`, `l2_reg_embedding`, `init_std=0.0001`, `seed=1024`, `task='binary'`, `device='cpu'`, and `gpus=None`. Always check the model-specific parameter names below before swapping model families.

| Model | Signature |
|---|---|
| `WDL` | `WDL(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(256, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None)` |
| `DeepFM` | `DeepFM(linear_feature_columns, dnn_feature_columns, use_fm=True, dnn_hidden_units=(256, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None)` |
| `xDeepFM` | `xDeepFM(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(256, 256), cin_layer_size=(256, 128), cin_split_half=True, cin_activation='relu', l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, l2_reg_cin=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None)` |
| `AFM` | `AFM(linear_feature_columns, dnn_feature_columns, use_attention=True, attention_factor=8, l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_att=1e-5, afm_dropout=0, init_std=0.0001, seed=1024, task='binary', device='cpu', gpus=None)` |
| `AFN` | `AFN(linear_feature_columns, dnn_feature_columns, ltl_hidden_size=256, afn_dnn_hidden_units=(256, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', task='binary', device='cpu', gpus=None)` |
| `AutoInt` | `AutoInt(linear_feature_columns, dnn_feature_columns, att_layer_num=3, att_head_num=2, att_res=True, dnn_hidden_units=(256, 128, 64), dnn_activation='relu', l2_reg_linear=1e-5, l2_reg_dnn=0, l2_reg_embedding=1e-5, dnn_use_bn=False, dnn_dropout=0, init_std=0.0001, seed=1024, task='binary', device='cpu', gpus=None, att_embedding_size=8)` |
| `DCN` | `DCN(linear_feature_columns, dnn_feature_columns, cross_num=2, cross_parameterization='vector', dnn_hidden_units=(128, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_cross=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None)` |
| `DCNMix` | `DCNMix(linear_feature_columns, dnn_feature_columns, cross_num=2, dnn_hidden_units=(128, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_cross=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, low_rank=32, num_experts=4, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None)` |
| `FiBiNET` | `FiBiNET(linear_feature_columns, dnn_feature_columns, bilinear_type='interaction', reduction_ratio=3, dnn_hidden_units=(128, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', task='binary', device='cpu', gpus=None)` |
| `IFM` | `IFM(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(256, 128), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None)` |
| `DIFM` | `DIFM(linear_feature_columns, dnn_feature_columns, att_head_num=8, att_res=True, dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task='binary', device='cpu', gpus=None, att_embedding_size=8)` |
| `MLR` | `MLR(region_feature_columns, base_feature_columns=None, bias_feature_columns=None, region_num=4, l2_reg_linear=1e-5, init_std=0.0001, seed=1024, task='binary', device='cpu', gpus=None)` |
| `NFM` | `NFM(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(128, 128), l2_reg_embedding=1e-5, l2_reg_linear=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, bi_dropout=0, dnn_dropout=0, dnn_activation='relu', task='binary', device='cpu', gpus=None)` |
| `ONN` | `ONN(linear_feature_columns, dnn_feature_columns, dnn_hidden_units=(128, 128), l2_reg_embedding=1e-5, l2_reg_linear=1e-5, l2_reg_dnn=0, dnn_dropout=0, init_std=0.0001, seed=1024, dnn_use_bn=False, dnn_activation='relu', task='binary', device='cpu', gpus=None)` |
| `PNN` | `PNN(dnn_feature_columns, dnn_hidden_units=(128, 128), l2_reg_embedding=1e-5, l2_reg_dnn=0, init_std=0.0001, seed=1024, dnn_dropout=0, dnn_activation='relu', use_inner=True, use_outter=False, kernel_type='mat', task='binary', device='cpu', gpus=None)` |
| `CCPM` | `CCPM(linear_feature_columns, dnn_feature_columns, conv_kernel_width=(6, 5), conv_filters=(4, 4), dnn_hidden_units=(256,), l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0, dnn_dropout=0, init_std=0.0001, seed=1024, task='binary', device='cpu', dnn_use_bn=False, dnn_activation='relu', gpus=None)` |

## Constructor exceptions and defaults

- `PNN` starts with `dnn_feature_columns`; do not pass `linear_feature_columns`.
- `MLR` starts with `region_feature_columns`; optional `base_feature_columns` default to the region columns, and optional `bias_feature_columns` default to an empty list.
- `AFN` uses `afn_dnn_hidden_units`, not `dnn_hidden_units`.
- `DeepFM` has `use_fm=True`; setting `use_fm=False` disables the FM branch.
- `DCN` supports `cross_parameterization='vector'` and `'matrix'`.
- `PNN.kernel_type` must be `mat`, `vec`, or `num`.
- `MLR.region_num` must be greater than 1.

## Base training API

### `compile`

```python
model.compile(optimizer, loss=None, metrics=None)
```

Supported optimizer strings:

```text
sgd, adam, adagrad, rmsprop
```

Supported loss strings:

```text
binary_crossentropy, mse, mae
```

Supported metric strings:

```text
binary_crossentropy, logloss, auc, mse, accuracy, acc
```

Behavior:

- Optimizer strings create `torch.optim.SGD(lr=0.01)`, `torch.optim.Adam()`, `torch.optim.Adagrad()`, or `torch.optim.RMSprop()`.
- `binary_crossentropy` maps to `torch.nn.functional.binary_cross_entropy`.
- `mse` maps to `torch.nn.functional.mse_loss`.
- `mae` maps to `torch.nn.functional.l1_loss`.
- `binary_crossentropy` and `logloss` metrics use sklearn log loss with manual clipping for newer sklearn compatibility.
- `auc` uses sklearn `roc_auc_score` and requires both classes in the evaluated labels.
- `accuracy` and `acc` threshold predictions at `0.5`.

### `fit`

```python
history = model.fit(
    x=None,
    y=None,
    batch_size=None,
    epochs=1,
    verbose=1,
    initial_epoch=0,
    validation_split=0.0,
    validation_data=None,
    shuffle=True,
    callbacks=None,
)
```

Key behavior:

- Dictionary inputs are converted to a feature-ordered list with `x = [x[feature] for feature in self.feature_index]`.
- One-dimensional feature arrays are expanded to column arrays.
- For single-task models, predictions with shape `(batch, 1)` are squeezed for loss computation.
- Targets with shape `(n, 1)` are squeezed for single-task loss computation.
- Returned `history` is a `History` callback with `history.history` and `history.epoch`.

### `predict`

```python
pred = model.predict(x, batch_size=256)
```

- Accepts dictionary input or a feature-ordered list.
- Returns concatenated NumPy `float64` predictions, usually shape `(n_samples, 1)`.

### `evaluate`

```python
result = model.evaluate(x, y, batch_size=256)
```

- Calls `predict` internally.
- Returns `{metric_name: metric_value}` for the compiled metrics.
- Flattens `y_true` and `y_pred` before metric functions.

## Callback API

### `EarlyStopping`

```python
EarlyStopping(
    monitor='val_loss',
    min_delta=0,
    patience=0,
    verbose=0,
    mode='auto',
    baseline=None,
    restore_best_weights=False,
)
```

- `mode='auto'` maximizes monitor names containing `acc`, ending with `auc`, or starting with `fmeasure`; otherwise it minimizes.
- Missing monitored metrics are ignored.
- `restore_best_weights=True` stores and restores `state_dict()` when an improvement occurs.

### `ModelCheckpoint`

```python
ModelCheckpoint(
    filepath,
    monitor='val_loss',
    verbose=0,
    save_best_only=False,
    save_weights_only=False,
    mode='auto',
    period=1,
)
```

- `filepath` can contain format fields such as `{epoch}` and metric names from logs.
- Creates the output directory if needed.
- With `save_weights_only=True`, saves `model.state_dict()`.
- With `save_weights_only=False`, saves the full model object.
- With `save_best_only=True`, skips saving when the monitored metric is missing.

## Prediction-layer task behavior

- `task='binary'`: output receives sigmoid, so predictions are probability-like values in `[0, 1]`.
- `task='regression'`: output is a raw scalar; choose `mse` or `mae`.
- These single-task workflows do not cover multi-class classification contracts.

## Public import note

`deepctr_torch.utils` imports `requests` and starts a best-effort PyPI version check in a background thread. If an environment imports `deepctr_torch` without `requests`, install `requests` or use an environment that includes it. Offline environments may print a manual version-check message; this does not by itself indicate that modeling APIs are unavailable.
