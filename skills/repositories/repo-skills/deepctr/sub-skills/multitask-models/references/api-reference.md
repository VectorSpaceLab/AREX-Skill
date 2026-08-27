# API Reference

## Shared multitask contract

All four model constructors share one feature graph:

- pass a single `dnn_feature_columns` iterable
- build one shared `model_input` mapping for all tasks
- return one `tf.keras.Model` with one output tensor per task
- each output tensor has shape `(None, 1)`
- `predict()` returns a list of numpy arrays in output order
- `fit()` accepts either:
  - a list/tuple of targets in output order, or
  - a dict keyed by `model.output_names`

For list-based losses, metrics, and targets, the order must match
`model.output_names`. For dict-based losses and metrics, the keys must match
those output names exactly.

## Constructor summary

| Model | Constructor | Default task contract | Output order |
|---|---|---|---|
| `SharedBottom` | `SharedBottom(dnn_feature_columns, bottom_dnn_hidden_units=(256, 128), tower_dnn_hidden_units=(64,), l2_reg_embedding=0.00001, l2_reg_dnn=0, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task_types=('binary', 'binary'), task_names=('ctr', 'ctcvr'))` | `task_types` may contain `binary` or `regression`; `len(task_types)` must equal `len(task_names)`; `len(task_names) > 1` | Same as `task_names` |
| `ESMM` | `ESMM(dnn_feature_columns, tower_dnn_hidden_units=(256, 128, 64), l2_reg_embedding=0.00001, l2_reg_dnn=0, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task_types=('binary', 'binary'), task_names=('ctr', 'ctcvr'))` | `len(task_names) == 2`; both task types must be `binary` | Fixed as `[task_names[0], task_names[1]]` |
| `MMOE` | `MMOE(dnn_feature_columns, num_experts=3, expert_dnn_hidden_units=(256, 128), tower_dnn_hidden_units=(64,), gate_dnn_hidden_units=(), l2_reg_embedding=0.00001, l2_reg_dnn=0, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task_types=('binary', 'binary'), task_names=('ctr', 'ctcvr'))` | `num_experts > 1`; `len(task_types)` must equal `len(task_names)`; each task type may be `binary` or `regression`; `len(task_names) > 1` | Same as `task_names` |
| `PLE` | `PLE(dnn_feature_columns, shared_expert_num=1, specific_expert_num=1, num_levels=2, expert_dnn_hidden_units=(256,), tower_dnn_hidden_units=(64,), gate_dnn_hidden_units=(), l2_reg_embedding=0.00001, l2_reg_dnn=0, seed=1024, dnn_dropout=0, dnn_activation='relu', dnn_use_bn=False, task_types=('binary', 'binary'), task_names=('ctr', 'ctcvr'))` | `len(task_types)` must equal `len(task_names)`; each task type may be `binary` or `regression`; `len(task_names) > 1` | Same as `task_names` |

## Validation rules

### SharedBottom, MMOE, PLE

- `num_tasks` is derived from `len(task_names)`.
- `num_tasks` must be greater than 1.
- `len(task_types)` must equal `num_tasks`.
- Each task type must be either `binary` or `regression`.
- The task name order is the output order.

### ESMM

- `task_names` must contain exactly two entries.
- Both task types must be `binary`.
- The output order is always the first name followed by the second name.
- The second output is the `CTR × CVR` product, so ESMM is specialized for
  click/conversion style workflows.

## Compile / fit / predict patterns

### List style

```python
model.compile(
    optimizer="adam",
    loss=["binary_crossentropy", "binary_crossentropy"],
)
model.fit(x, [y0, y1], batch_size=32, epochs=1, verbose=0)
preds = model.predict(x, batch_size=32, verbose=0)
```

Use list targets only when the loss list and target list are already aligned to
`model.output_names`.

### Dict style

```python
losses = {name: "binary_crossentropy" for name in model.output_names}
targets = {name: y for name, y in zip(model.output_names, [y0, y1])}

model.compile(optimizer="adam", loss=losses)
model.fit(x, targets, batch_size=32, epochs=1, verbose=0)
preds = model.predict(x, batch_size=32, verbose=0)
```

Use dicts when you want to avoid manual order bookkeeping.

## Named-output reminders

- `task_names` are output-layer names, not just labels.
- `model.output_names` is the safest source of truth for order-sensitive code.
- `predict()` returns a list, even when the output names are custom.
- If you need a mixed binary/regression multitask model, use SharedBottom,
  MMOE, or PLE. ESMM is binary-only.

## Minimal output-shape expectations

For a batch of size `N`:

- `model.output_names` has length 2 or more, depending on the model.
- each prediction array has shape `(N, 1)`
- `fit()` accepts one target per output
- `evaluate()` accepts the same target structure as `fit()`

