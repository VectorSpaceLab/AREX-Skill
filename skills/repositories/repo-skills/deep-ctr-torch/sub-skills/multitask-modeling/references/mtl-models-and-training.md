# Multi-task models and training

This reference covers the implemented DeepCTR-Torch multi-task learning classes: `SharedBottom`, `ESMM`, `MMOE`, and `PLE`.

## Minimal workflow

1. Build one shared feature-column set and one `model_input` dictionary. Use `../../feature-column-inputs/SKILL.md` for feature-column construction and input alignment.
2. Choose an MTL class from the table below.
3. Define `task_names` in the exact column order you want predictions returned.
4. Build a target matrix `y` shaped `(n_samples, len(task_names))`.
5. Compile with a loss list in the same order as `task_names`.
6. Fit and predict. Treat `pred[:, i]` as the prediction for `task_names[i]`.

```python
from deepctr_torch.models import MMOE

model = MMOE(
    dnn_feature_columns,
    task_types=['binary', 'binary'],
    task_names=['finish', 'like'],
    num_experts=3,
    expert_dnn_hidden_units=(256, 128),
    gate_dnn_hidden_units=(64,),
    tower_dnn_hidden_units=(64,),
    device='cpu',
)
model.compile(
    'adagrad',
    loss=['binary_crossentropy', 'binary_crossentropy'],
    metrics=['binary_crossentropy'],
)
history = model.fit(train_model_input, train[['finish', 'like']].values, batch_size=32, epochs=1)
pred = model.predict(test_model_input, batch_size=256)
assert pred.shape == (len(test_rows), 2)
finish_pred = pred[:, 0]
like_pred = pred[:, 1]
```

## Model choice

| Model | Use when | Tasks | Output columns | Important constraints |
| --- | --- | --- | --- | --- |
| `SharedBottom` | Tasks can share one bottom DNN and only need separate towers. | More than one binary/regression task. | One column per `task_names` entry. | `dnn_feature_columns` must be non-empty. |
| `MMOE` | Task relatedness is uncertain and each task should learn its own gate over shared experts. | More than one binary/regression task. | One column per `task_names` entry. | `num_experts` must be greater than 1; `dnn_feature_columns` must be non-empty. |
| `PLE` | You need both shared and task-specific experts with progressive gating. | More than one binary/regression task. | One column per `task_names` entry. | Use tested expert-count combinations before relying on asymmetric shared/specific counts. |
| `ESMM` | You are modeling the impression → click → conversion chain. | Exactly two binary tasks. | Column 0 is CTR; column 1 is CTCVR. | `ESMM` computes `CTCVR = CTR * CVR`; train against click and click-and-conversion labels, not an isolated clicked-only CVR label. |

## Target matrix contract

The multi-task tests generate labels by making one vector per task and transposing them into `(sample_size, num_tasks)`:

```python
import numpy as np

y_finish = np.array([1, 0, 1, 0], dtype='float32')
y_like = np.array([0, 0, 1, 1], dtype='float32')
y = np.array([y_finish, y_like]).T
assert y.shape == (4, 2)
```

For a pandas workflow, use an ordered list:

```python
task_names = ['finish', 'like']
y_train = train[task_names].values.astype('float32')
y_test = test[task_names].values.astype('float32')
```

Do not pass a one-dimensional target vector to a multi-task model. A one-dimensional target has no task axis, so the training loop cannot align `y[:, i]` with task `i`.

## Compile, losses, and metrics

Supported loss strings are inherited from the shared training API:

- `binary_crossentropy` for `task_types[i] == 'binary'`
- `mse` or `mae` for `task_types[i] == 'regression'`

Use a loss list whenever the model has multiple tasks:

```python
# Two binary tasks
model.compile('adam', ['binary_crossentropy', 'binary_crossentropy'], metrics=['binary_crossentropy'])

# Mixed binary + regression task order
model = MMOE(
    dnn_feature_columns,
    task_types=['binary', 'regression'],
    task_names=['clicked', 'watch_time'],
)
model.compile('adam', ['binary_crossentropy', 'mse'], metrics=[])
```

Metric caveat: the shared `BaseModel` metric path flattens two-dimensional `y_true` and `y_pred` before calling metric functions. That makes a metric such as `binary_crossentropy` a single aggregate across all task columns, and makes global `auc` inappropriate for mixed binary/regression outputs. For reliable reporting, call `predict`, then compute metrics column-by-column with `task_names` order.

```python
pred = model.predict(test_model_input, batch_size=256)
for i, name in enumerate(task_names):
    task_y = y_test[:, i]
    task_pred = pred[:, i]
    # compute the metric suitable for this one task only
```

## ByteRec-style two-target recipe

A common two-target recipe uses ByteRec-like columns where `finish` and `like` are binary labels and the same sparse/dense features feed both tasks.

```python
sparse_features = ['uid', 'user_city', 'item_id', 'author_id', 'item_city', 'channel', 'music_id', 'device']
dense_features = ['duration_time']
task_names = ['finish', 'like']

# Encode sparse features and scale dense features before creating feature columns.
# See ../../feature-column-inputs/SKILL.md for exact feature-column construction.

feature_names = get_feature_names(dnn_feature_columns)
train_model_input = {name: train[name] for name in feature_names}
test_model_input = {name: test[name] for name in feature_names}

y_train = train[task_names].values.astype('float32')

model = MMOE(
    dnn_feature_columns,
    task_types=['binary', 'binary'],
    task_names=task_names,
    l2_reg_embedding=1e-5,
    device=device,
)
model.compile('adagrad', ['binary_crossentropy', 'binary_crossentropy'], metrics=['binary_crossentropy'])
model.fit(train_model_input, y_train, batch_size=32, epochs=1)
pred = model.predict(test_model_input, 256)

for i, task_name in enumerate(task_names):
    task_predictions = pred[:, i]
```

## Tower, gate, and expert parameters

- `tower_dnn_hidden_units` controls task-specific layers before each final prediction layer.
- `MMOE` has `num_experts`, `expert_dnn_hidden_units`, a per-task gate DNN, and per-task towers. Native coverage includes empty `gate_dnn_hidden_units=()` and/or `tower_dnn_hidden_units=()`.
- `PLE` has shared experts, task-specific experts, CGC levels, gates, and towers. Native coverage uses equal `shared_expert_num` and `specific_expert_num`; validate custom asymmetric counts in your environment before using them in production.
- `SharedBottom` has one shared bottom DNN followed by per-task towers. Native coverage includes `tower_dnn_hidden_units=()`.
- `ESMM` uses two binary towers to derive CTR and CVR internally, then outputs CTR and CTCVR. Keep `tower_dnn_hidden_units` non-empty because the implementation uses the final tower width.

## Tiny batch behavior

CPU tests cover `MMOE` and `PLE` with `batch_size=1` for fit and predict, and both assert prediction shape `(sample_size, 2)`. Keep `dnn_use_bn=False` for tiny batches unless you have validated BatchNorm behavior for your batch size.
