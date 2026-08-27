# Multi-task troubleshooting

Use this page when a `SharedBottom`, `ESMM`, `MMOE`, or `PLE` run fails or produces confusing multi-output results.

## Fast checks

```python
assert len(task_names) >= 2
assert y.ndim == 2
assert y.shape[1] == len(task_names)
assert len(task_types) == len(task_names)
assert len(loss_list) == len(task_names)
pred = model.predict(model_input, batch_size=256)
assert pred.shape == (len(y), len(task_names))
```

For `ESMM`:

```python
assert len(task_names) == 2
assert task_types == ['binary', 'binary'] or task_types == ('binary', 'binary')
# output column 0 is CTR; output column 1 is CTCVR, not raw CVR
```

## Symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Target indexing error during `fit`, or shape mismatch between `y_pred` and `y`. | A one-dimensional target vector was passed to a multi-task model. | Build `y` as `(n_samples, num_tasks)`, for example `data[task_names].values.astype('float32')`. |
| Prediction columns seem swapped. | `task_names` order and label matrix column order differ. | Set `task_names` once and derive labels with that same list: `y = data[task_names].values`; read predictions as `pred[:, i]` for `task_names[i]`. |
| `ValueError: num_tasks must be equal to the length of task_types`. | `len(task_types) != len(task_names)`. | Add or remove task type entries so each task has exactly one type. |
| Assertion about `loss_func` length. | Compile used a loss list whose length differs from the number of tasks. | Use one loss per task in task order, e.g. `['binary_crossentropy', 'mse']`. |
| `NotImplementedError` from loss selection. | Loss string is unsupported. | Use only `binary_crossentropy`, `mse`, or `mae`, or pass a compatible callable. |
| `ValueError: task must be binary or regression`. | `SharedBottom`, `MMOE`, or `PLE` received an unsupported task type such as multiclass. | Restrict to `binary` and `regression`; do not use these classes for arbitrary multiclass task graphs without custom model code. |
| `ValueError: task must be binary in ESMM`. | `ESMM` was given a non-binary task type. | Use `ESMM` only for two binary tasks. Use `MMOE`, `PLE`, or `SharedBottom` for binary/regression mixtures. |
| `ESMM` second prediction looks too low or does not match CVR labels. | The second ESMM output is CTCVR (`CTR * CVR`), not raw CVR. | Train with click labels in column 0 and click-and-conversion labels in column 1. Evaluate raw CVR separately only if you derive it intentionally. |
| Global `auc` is invalid or misleading for mixed tasks. | Shared metrics flatten all task columns before metric calculation. | Set `metrics=[]` or use only coarse aggregate metrics during training; compute per-task metrics after `predict`. |
| AUC/log-loss fails on very small batches. | A batch or flattened metric input can contain only one class. | Avoid `auc` in training metrics for tiny data. Use `metrics=['binary_crossentropy']` or no metrics, then evaluate per task on a larger prediction set. |
| `dnn_feature_columns is null!`. | The MTL constructor received an empty feature-column list. | Build and pass non-empty `dnn_feature_columns`; route feature construction to the feature-column input sub-skill. |
| `MMOE` reports `num_experts must be greater than 1`. | `num_experts <= 1`. | Use at least two experts, for example `num_experts=2` or `3`. |
| `ESMM` fails when tower hidden units are empty. | The implementation indexes the final tower width. | Keep `tower_dnn_hidden_units` non-empty for `ESMM`, such as `(256, 128)` or a smaller smoke-test tuple. |
| Tiny `batch_size=1` works without BatchNorm but fails with BatchNorm settings. | BatchNorm can be unstable or invalid with one-sample batches. | Keep `dnn_use_bn=False` for tiny smoke tests, or increase batch size. |
| `PLE` fails with unusual shared/specific expert counts. | Native coverage uses equal `shared_expert_num` and `specific_expert_num`; custom asymmetric counts need validation in the installed version. | Start with equal counts such as `(1, 1)` or `(3, 3)`, then add a focused smoke test before production use. |

## Difficult case 1: one-dimensional target array

Wrong:

```python
task_names = ['finish', 'like']
y = data['finish'].values  # shape: (n_samples,)
model.fit(model_input, y, batch_size=32, epochs=1)
```

Correct:

```python
task_names = ['finish', 'like']
y = data[task_names].values.astype('float32')
assert y.shape == (len(data), 2)
model = MMOE(dnn_feature_columns, task_types=['binary', 'binary'], task_names=task_names)
model.compile('adam', ['binary_crossentropy', 'binary_crossentropy'])
model.fit(model_input, y, batch_size=32, epochs=1)
pred = model.predict(model_input, batch_size=256)
assert pred.shape == (len(data), 2)
```

## Difficult case 2: mixed binary and regression targets

Use `MMOE`, `PLE`, or `SharedBottom`; do not use `ESMM`.

```python
task_names = ['clicked', 'watch_time']
task_types = ['binary', 'regression']
losses = ['binary_crossentropy', 'mse']
y = data[task_names].values.astype('float32')

model = PLE(
    dnn_feature_columns,
    task_types=task_types,
    task_names=task_names,
    shared_expert_num=1,
    specific_expert_num=1,
)
model.compile('adam', losses, metrics=[])
model.fit(model_input, y, batch_size=64, epochs=1)
pred = model.predict(model_input, batch_size=256)

clicked_pred = pred[:, 0]
watch_time_pred = pred[:, 1]
```

Recommended metric handling:

- Compute binary metrics only on `clicked_pred` and `y[:, 0]`.
- Compute regression metrics only on `watch_time_pred` and `y[:, 1]`.
- Avoid global training `auc` for mixed outputs because the shared API flattens columns before metric calculation.

## Batch-size-one edge case

`MMOE` and `PLE` are covered for `batch_size=1` fit/predict when `dnn_use_bn=False` and two binary labels are shaped `(sample_size, 2)`. If reproducing this edge case, keep the setup minimal:

```python
model.compile('adam', ['binary_crossentropy', 'binary_crossentropy'], metrics=['binary_crossentropy'])
history = model.fit(model_input, y, batch_size=1, epochs=1, verbose=0)
assert 'loss' in history.history
pred = model.predict(model_input, batch_size=1)
assert pred.shape == (len(y), 2)
```
