# Training and Persistence Troubleshooting

Use this guide to convert common TFLearn training, feed, validation,
TensorBoard, checkpoint, and restore failures into concrete fixes.

## Fast Diagnostic Snippets

Run these inside the graph before `DNN(...)` or before a suspicious `fit(...)`:

```python
import tensorflow.compat.v1 as tf

print('inputs:', [t.name for t in tf.get_collection(tf.GraphKeys.INPUTS)])
print('targets:', [t.name for t in tf.get_collection(tf.GraphKeys.TARGETS)])
print('train_ops:', [getattr(op, 'name', None) for op in tf.get_collection(tf.GraphKeys.TRAIN_OPS)])
print('variables:', [v.name for v in tf.global_variables()[:20]])
```

For checkpoint files:

```python
import os
stem = '/tmp/exp/model.tfl'
print(os.path.exists(stem + '.index'), stem)
```

## Setup and Compatibility Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Import fails on modern TensorFlow with missing `tensorflow.python.util.nest.is_sequence`. | TFLearn 0.5.0 targets TensorFlow 1.x internals. | Use a TensorFlow 1.15.x-compatible environment for this repo skill. Do not treat TensorFlow 2.x as verified. |
| Protobuf descriptor errors while importing TensorFlow 1.15.5. | Incompatible protobuf 4.x with TensorFlow 1.15.5. | Use protobuf 3.20.x in the TF1 environment. |
| Device placement/GPU errors. | CUDA setup is optional/unverified here; CPU is the verified backend. | Use CPU for correctness. If using GPU, keep `soft_placement=True` in `tflearn.init_graph(...)` and treat placement logs/performance as environment-specific. |

## Missing Graph Collections

### `No input data! Please add an 'input_data' layer...`

Cause: `tflearn.DNN(network)` checks `tf.GraphKeys.INPUTS` and found no input
placeholder.

Fix:

```python
x = tflearn.input_data(shape=[None, n_features], name='input')
# or wrap an existing placeholder:
ph = tf.placeholder(tf.float32, [None, n_features], name='input')
x = tflearn.input_data(placeholder=ph)
```

If using custom TensorFlow placeholders without `input_data`, manually adding to
collections is possible but less portable; prefer `tflearn.input_data`.

### `tf collection "train_op" is empty... regression layer`

Cause: `DNN.fit(...)` found no `TrainOp` in `tf.GraphKeys.TRAIN_OPS`.
Typically the final graph tensor was never passed through `tflearn.regression`.

Fix:

```python
net = tflearn.fully_connected(x, 1)
net = tflearn.regression(net, optimizer='sgd', loss='mean_square',
                         learning_rate=0.01, name='target')
model = tflearn.DNN(net)
model.fit({'input': X}, {'target': Y})
```

## Feed Dictionary and Ordering Problems

### Unknown feed-dict names

Signal:

```text
Feed dict asks for variable named 'non_existent' but no such variable is known to exist
```

Cause: a string key in `X_inputs` or `Y_targets` did not resolve to a known
input/target placeholder.

Fix:

1. Inspect names:

   ```python
   print([t.name for t in tf.get_collection(tf.GraphKeys.INPUTS)])
   print([t.name for t in tf.get_collection(tf.GraphKeys.TARGETS)])
   ```

2. Use the layer name, exact placeholder tensor name, or tensor object:

   ```python
   model.fit({'input': X}, {'target': Y})       # input/X:0, target/Y:0
   model.fit({'input1:0': X1}, {'target': Y})   # custom placeholder name
   model.fit({input_ph: X}, {target_ph: Y})     # tensor keys
   ```

3. If names have a variable-scope prefix, include it in the key:
   `{'scopeQ/input': X}` and `{'scopeQ/target': Y}` can be needed for scoped
   `input_data(name='input')` and `regression(name='target')`.

### List feeds train the wrong input/target

Cause: lists are matched by placeholder creation order, not by variable names.
Repeated notebook cells can also leave old placeholders in the default graph.

Fix:

- Prefer dictionaries for multi-input or multi-target models.
- Wrap graph construction in `with tf.Graph().as_default():` for scripts/tests.
- In notebooks, call `tf.reset_default_graph()` before rebuilding.
- Print collection order when a list feed is unavoidable:

  ```python
  print('input order:', [t.name for t in tf.get_collection(tf.GraphKeys.INPUTS)])
  print('target order:', [t.name for t in tf.get_collection(tf.GraphKeys.TARGETS)])
  ```

### Multiple inputs but only one data object

Cause: the graph has more than one input placeholder and `X_inputs` was not a
list/dict with the same count.

Fix:

```python
model.fit([X1, X2], Y)                         # creation-order list
model.fit({'input1': X1, 'input2': X2}, Y)      # named dict
model.fit({ph1: X1, ph2: X2}, {target_ph: Y})  # tensor dict
```

## Validation and Snapshot Problems

| Symptom | Cause | Fix |
|---|---|---|
| `validation_set must be a tuple or list...` | Passed a non-float, non-tuple/list validation object to `DNN.fit`. | Use `validation_set=0.1` or `validation_set=(valX, valY)`. |
| Validation OOM or slow validation. | Validation defaults to training batch size unless overridden. | Set `validation_batch_size` in `DNN.fit` or `validation_batch_size` in `regression`/`TrainOp`. |
| No validation metrics appear. | No validation data, `snapshot_epoch=False`, `snapshot_step=None`, or metric disabled. | Provide validation data, enable at least one snapshot trigger, and set `show_metric=True` with a valid metric. |
| Best checkpoint never appears. | `best_checkpoint_path` requires validation accuracy (`val_acc`) to be non-`None` and above `best_val_accuracy`. | Use a classification metric or valid metric, `show_metric=True`, validation data, and a realistic threshold. |
| Auto-checkpoints not written. | `checkpoint_path=None`, snapshots disabled, or path unwritable. | Set a writable `checkpoint_path` stem and `snapshot_epoch=True` or `snapshot_step=N`. |

Remember: a snapshot can evaluate/log without saving when no `checkpoint_path`
is configured.

## TensorBoard and Log Directory Problems

### Cannot find TensorBoard event files

TFLearn prints both a run id and base log directory:

```text
Run id: run_001
Log directory: /tmp/tflearn_logs/
```

The writer is created under `<tensorboard_dir>/<run_id>`. Try:

```bash
find /tmp/tflearn_logs -maxdepth 2 -type f -name 'events.out.tfevents*'
tensorboard --logdir /tmp/tflearn_logs
```

If no files appear:

- Ensure `fit(...)` actually ran at least one batch.
- Use a writable `tensorboard_dir`.
- Avoid accidentally writing under a relative path from an unexpected current
  directory.
- Reduce `tensorboard_verbose` to `0` if summary creation is slowing or
  destabilizing a tiny smoke.

## Graph and Session Reuse Problems

### Re-running notebook cells causes shape/feed weirdness

Cause: default graph collections accumulate old `input_data`, target, train-op,
and variable objects.

Fix:

```python
tf.reset_default_graph()
# rebuild graph, then construct DNN
```

In scripts/tests, prefer:

```python
with tf.Graph().as_default():
    # build and train one model
```

### Loading multiple checkpoints into one combined graph loses earlier restore

Cause: `DNN.load`/`Trainer.restore` defaults to `create_new_session=True`, which
closes the current session, creates a new one, and reinitializes variables.

Fix: keep the session on subsequent loads:

```python
model.load(model1_stem, scope_for_restore='scope1', weights_only=True)
model.load(model2_stem, scope_for_restore='scope2', weights_only=True,
           create_new_session=False)
```

### Existing session passed to `DNN` has uninitialized variables

Cause: `DNN(..., session=session)` treats the session as restored/owned and does
not initialize variables for you.

Fix: initialize before passing it, or let `DNN` create the session.

```python
sess = tf.Session()
sess.run(tf.global_variables_initializer())
model = tflearn.DNN(net, session=sess)
```

## Restore and Checkpoint Failures

### Loading `.index` instead of stem

Signal: TensorFlow cannot find the checkpoint or complains about invalid files.

Fix:

```python
model.load('/tmp/exp/model.tfl')        # correct
# not: model.load('/tmp/exp/model.tfl.index')
```

### `NotFoundError` for variables after adding a scope

Cause: current graph variable names differ from checkpoint names.

Fix options:

```python
# Current variables are scopeA/..., file variables were unscoped:
model.load(stem, scope_for_restore='scopeA', weights_only=True, verbose=True)

# Current variables are scopeA/..., file variables are scopeQ/...:
model.load(stem, variable_name_map=('scopeA', 'scopeQ'), verbose=True)
```

See [checkpointing](checkpointing.md#restore-into-renamed-variable-scopes) for
function maps and multi-scope loading.

### Missing optimizer slots or moving averages

Cause: using `weights_only=True`, `regression(..., restore=False)`, or variables
created with `restore=False` excludes non-trainable state.

Fix:

- For exact resume, use `weights_only=False` and matching graph/training ops.
- For transfer/subnet restore, keep `weights_only=True` and expect optimizer
  state to be newly initialized.

### Shape mismatch on restore or `set_weights`

Cause: graph architecture changed or the target variable has a different shape.

Fix:

- Rebuild the same layer sizes before full restore.
- Use a mapping function returning `None` for incompatible variables when doing
  partial transfer.
- Inspect variables and checkpoint names/sizes with TensorFlow checkpoint tools
  in the user's environment when necessary.

## Prediction and Evaluation Issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Dropout/batch-normalization behaves as if training during prediction. | Custom graph did not use TFLearn training-mode variable correctly. | Use TFLearn layers or wrap custom behavior with `tflearn.get_training_mode()`; `DNN.predict`/`Evaluator` set training mode false. |
| `evaluate` returns odd values or errors. | Regression metric is `None`, targets missing, or feed shape incompatible. | Confirm `regression(..., metric=...)`, inspect target placeholders, and run `model.predict` first to validate input shapes. |
| Prediction shape surprises. | Final network tensor shape determines output; multi-output `Evaluator` concatenates/list-builds outputs. | Print `model.net.get_shape()` and test with a tiny batch. |

## Minimal Recovery Checklist

When a user asks to fix a broken training/persistence script:

1. Put graph construction in a fresh graph or reset the default graph.
2. Verify `input_data` and `regression` collections.
3. Replace list feeds with named dicts or tensor-key dicts.
4. Use explicit writable `tensorboard_dir` and checkpoint/save stems.
5. Disable snapshots for fast smoke: `snapshot_epoch=False`, unless testing
   checkpointing.
6. For restore, load the checkpoint stem and either match variable names exactly
   or supply `scope_for_restore`/`variable_name_map`.
7. Prove success with `predict`/`evaluate` after training and after restore.
