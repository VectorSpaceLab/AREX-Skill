# Single-task troubleshooting

Use this reference for predictable failures in binary classification and scalar regression workflows. For feature-name, feature-column, dense-width, sparse-vocabulary, or sequence-padding issues, route to [`../../feature-column-inputs/SKILL.md`](../../feature-column-inputs/SKILL.md).

## Task, loss, and metric mismatch

Symptoms:

- `binary_cross_entropy` errors with regression targets outside `[0, 1]`.
- `auc` or `accuracy` looks meaningless for rating prediction.
- Binary predictions are unbounded, or regression predictions are squeezed into probabilities.

Fix:

| Goal | Constructor | Compile |
|---|---|---|
| Binary CTR/click prediction | `task='binary'` | `model.compile('adagrad', 'binary_crossentropy', metrics=['binary_crossentropy', 'auc'])` |
| Regression ratings/values | `task='regression'` | `model.compile('adam', 'mse', metrics=['mse'])` |

If converting a binary DeepFM example to ratings, update all of these at the same time: model `task`, loss, metrics, target column, and downstream evaluation. See [training and prediction](training-and-prediction.md#convert-binary-deepfm-to-regression-ratings).

## AUC fails on a tiny or single-class validation split

Symptom:

```text
ValueError: Only one class present in y_true. ROC AUC score is not defined in that case.
```

Cause:

DeepCTR-Torch maps metric string `auc` to sklearn `roc_auc_score`. AUC requires both positive and negative labels in the evaluated labels. With `validation_split`, the validation set is taken from the last fraction of arrays before training; a tiny split can easily contain only one class. Batch-level training metrics can also fail when a batch has one class.

Fix options:

1. Use an explicit stratified validation set with both classes and pass `validation_data=(val_x, val_y)`.
2. Increase validation size or batch size so each metric call is likely to contain both classes.
3. During tiny smoke tests, compile with `metrics=['binary_crossentropy']` and compute AUC once at the end only if both classes are present.
4. For regression, remove `auc` entirely.

## Target shape and column-vector support

Supported for single-task models:

```python
y = df['label'].values          # shape (n_samples,)
y = df[['label']].values        # shape (n_samples, 1)
```

The training loop squeezes `(batch, 1)` predictions and `(batch, 1)` targets for single-task loss computation. If errors persist, check that `y` is numeric and has exactly one target column. Multi-column labels belong to the multitask sub-skill.

## No linear part or no DNN part

DeepFM supports an intentionally missing linear part:

```python
model = DeepFM([], dnn_feature_columns, use_fm=True, dnn_hidden_units=(32,), task='binary', device=device)
```

This is useful for isolating the DNN/FM contribution. If the user expects a wide component, do not pass `[]`; pass the linear feature columns returned by the feature-column workflow.

For `PNN`, the absence of a linear part is normal because the constructor is:

```python
model = PNN(dnn_feature_columns, use_inner=True, use_outter=False, kernel_type='mat', task='binary')
```

## MLR special feature-column groups

Symptoms:

- User tries `MLR(linear_feature_columns, dnn_feature_columns)` by analogy with DeepFM.
- Input dictionary is missing features from one of the MLR groups.
- `region_num` errors.

Fix:

```python
model = MLR(
    region_feature_columns,
    base_feature_columns=base_feature_columns,
    bias_feature_columns=bias_feature_columns,
    region_num=4,
    task='binary',
    device=device,
)
```

Rules:

- `region_feature_columns` are required.
- `base_feature_columns` default to `region_feature_columns` when omitted or empty.
- `bias_feature_columns` default to no bias features when omitted.
- `region_num` must be greater than 1.
- The input dictionary must include every feature name from `region_feature_columns + base_feature_columns + bias_feature_columns`.

## `gpus[0]` must match `device`

Symptom:

```text
ValueError: `gpus[0]` should be the same gpu with `device`
```

Cause:

The base model checks that the first GPU id in `gpus` appears in the `device` string.

Fix:

```python
# Valid single GPU / first GPU match.
model = DeepFM(columns, columns, task='binary', device='cuda:0', gpus=[0])

# Valid multi-GPU / first GPU match.
model = DeepFM(columns, columns, task='binary', device='cuda:0', gpus=[0, 1])

# CPU fallback.
model = DeepFM(columns, columns, task='binary', device='cpu', gpus=None)
```

Do not use `device='cuda:1', gpus=[0, 1]`.

## Checkpoint save/load problems

Symptoms:

- No checkpoint file appears.
- Best-only checkpoint never saves.
- Load fails after moving between devices or changing feature columns.

Fix:

- Make sure the callback monitor exists in logs, e.g. `val_binary_crossentropy`, `val_auc`, `val_mse`, or `loss`.
- Use `validation_data` or `validation_split` when monitoring a `val_*` metric.
- Prefer `save_weights_only=True` and reconstruct the same model class with the same feature columns before loading weights.
- Use `torch.load(path, map_location=device)` when loading weights saved on a different device.
- If `save_best_only=True` and the monitor is missing, the checkpoint callback skips saving.

Safe pattern:

```python
ckpt = ModelCheckpoint(
    filepath='checkpoints/deepfm-{epoch:02d}.pt',
    monitor='val_binary_crossentropy',
    mode='min',
    save_best_only=True,
    save_weights_only=True,
)
```

## Missing `requests` import

Symptom:

```text
ModuleNotFoundError: No module named 'requests'
```

Cause:

`deepctr_torch.utils` imports `requests`, but the package metadata may not install it automatically in minimal environments.

Fix:

```bash
python -m pip install requests
```

Then re-run the import or smoke helper.

## Offline package version check message

Symptom:

```text
Please check the latest version manually on https://pypi.org/project/deepctr-torch/#history
```

Cause:

Importing DeepCTR-Torch starts a best-effort background check against PyPI. Offline or firewalled environments can print this message.

Fix:

- Treat it as informational if `import deepctr_torch` succeeds and modeling APIs import.
- For clean logs in offline CI, capture stdout/stderr or preinstall an environment that can import the package before running modeling jobs.

## PNN kernel type error

Symptom:

```text
ValueError: kernel_type must be mat,vec or num
```

Fix:

Use one of:

```python
PNN(dnn_feature_columns, kernel_type='mat')
PNN(dnn_feature_columns, kernel_type='vec')
PNN(dnn_feature_columns, kernel_type='num')
```

## Dense features unsupported in a DNN branch

Symptom:

```text
ValueError: DenseFeat is not supported in dnn_feature_columns
```

Cause:

Some model internals call `input_from_feature_columns(..., support_dense=False)` for interaction branches that require sparse embeddings. The exact failure depends on the model family and branch.

Fix:

- Confirm whether the selected model family supports dense features in the branch you are using.
- For sparse-only interaction models, keep dense features in linear/base components or choose a model family that supports dense DNN inputs.
- Revalidate feature columns with the feature-column sub-skill.

## Quick triage checklist

1. Is the workflow single-output? If no, route to multitask.
2. Is the model DIN or DIEN? If yes, route to sequence-interest.
3. Do all input dictionary keys match `get_feature_names(...)` or the MLR feature union?
4. Is `task` aligned with loss and metrics?
5. Does AUC see both classes in each metric call?
6. Is `device` available, and does `gpus[0]` match it?
7. Are checkpoint monitors present in `history.history`?
8. Can `import deepctr_torch` run with `requests` installed?
