# Training and Persistence API Reference

This reference covers the TFLearn 0.5.0 training and persistence APIs that are
most useful after a graph has already been built. It assumes a TensorFlow 1.x
runtime; the verified package/runtime pairing for this generated skill is
TFLearn 0.5.0, TensorFlow 1.15.5, and NumPy 1.18.5.

## Runtime and Graph Setup

```python
import tensorflow.compat.v1 as tf
import tflearn

# Optional graph/session config. Call before building the graph that should use it.
tflearn.init_graph(seed=None, log_device=False, num_cores=0,
                   gpu_memory_fraction=0, soft_placement=True)
```

Important setup rules:

- Use TensorFlow 1.x graph execution. Modern TensorFlow 2.x imports are not a
  drop-in runtime for this checkout.
- Start each independent model in a fresh graph:
  `with tf.Graph().as_default(): ...` or `tf.reset_default_graph()` before
  rebuilding in notebooks.
- `tflearn.input_data(...)` adds placeholders to `tf.GraphKeys.INPUTS`.
- `tflearn.regression(...)` adds target placeholders to `tf.GraphKeys.TARGETS`
  and a `TrainOp` to `tf.GraphKeys.TRAIN_OPS`.
- `tflearn.DNN(network)` raises if there is no input layer. `DNN.fit(...)`
  raises if the train-op collection is empty, usually because `regression` is
  missing.

## DNN Model Wrapper

Constructor:

```python
tflearn.DNN(network,
            clip_gradients=5.0,
            tensorboard_verbose=0,
            tensorboard_dir='/tmp/tflearn_logs/',
            checkpoint_path=None,
            best_checkpoint_path=None,
            max_checkpoints=None,
            session=None,
            best_val_accuracy=0.0)
```

Key constructor options:

| Option | Use |
|---|---|
| `network` | Final `tf.Tensor` returned by the model graph, normally after `tflearn.regression(...)`. |
| `clip_gradients` | Global gradient clipping value used while building train ops. Use `0.0` to disable clipping in lower-level `Trainer`/generator-style workflows. |
| `tensorboard_verbose` | Summary depth: `0` loss/metric, `1` + gradients, `2` + weights, `3` + activations/sparsity. Higher values are slower. |
| `tensorboard_dir` | Base directory where `Trainer.fit` creates a run subdirectory named by `run_id` or a generated id. |
| `checkpoint_path` | Stem used by automatic snapshots. If `None`, snapshots evaluate/log but do not save checkpoint files. |
| `best_checkpoint_path` | Stem prefix for best-validation saves when validation accuracy improves above `best_val_accuracy`. |
| `max_checkpoints` | Passed to TensorFlow `Saver(max_to_keep=...)`; `None` means no count limit. |
| `session` | Existing initialized `tf.Session`. If omitted, DNN creates and initializes a session. |

### Fit

Signature verified from the installed package/source:

```python
model.fit(X_inputs, Y_targets,
          n_epoch=10,
          validation_set=None,
          show_metric=False,
          batch_size=None,
          shuffle=None,
          snapshot_epoch=True,
          snapshot_step=None,
          excl_trainops=None,
          validation_batch_size=None,
          run_id=None,
          callbacks=[])
```

Input forms:

| Form | Meaning |
|---|---|
| `model.fit(X, Y)` | Single input and single target. |
| `model.fit([X1, X2], Y)` | Multiple inputs matched to input placeholders by creation order. |
| `model.fit(X, [Y1, Y2])` | Multiple targets matched to target placeholders by creation order. |
| `model.fit({'input': X}, {'target': Y})` | Named feed using layer/placeholder names. Preferred for non-trivial graphs. |
| `model.fit({input_tensor: X}, {target_tensor: Y})` | Direct TensorFlow placeholder keys. Most explicit and robust. |

Fit behavior to remember:

- `batch_size` overrides every collected `TrainOp.batch_size`; if
  `validation_batch_size` is omitted it also becomes the validation batch size.
- `validation_batch_size` overrides every collected `TrainOp.validation_batch_size`.
- `shuffle` overrides all `TrainOp.shuffle` values when it is a `bool`.
- `validation_set=0.1` splits each feed dictionary by shuffling the index array
  and holding out 10% of samples for validation.
- `validation_set=(valX, valY)` builds a separate validation feed dictionary
  with the same input/target naming or list-ordering rules as training.
- `snapshot_epoch=True` triggers end-of-epoch snapshots; `snapshot_step=N`
  triggers snapshots every `N` global training steps. A snapshot evaluates
  validation data when present and saves only if a checkpoint stem was supplied
  in the constructor.
- `run_id` is appended to `tensorboard_dir` for TensorBoard event files. If it
  is not supplied, TFLearn generates a short id.
- `callbacks` accepts one `tflearn.callbacks.Callback` or a list of callbacks;
  see [workflows](workflows.md#callbacks-and-training-state).

### Predict, Evaluate, Save, Load

```python
pred = model.predict(X)
score = model.evaluate(X, Y, batch_size=128)
model.save('/path/to/model-stem.tflearn')
model.load('/path/to/model-stem.tflearn', weights_only=False, **restore_options)
```

- `predict(X)` accepts the same input forms as `fit` without targets. It returns
  a NumPy array for one output tensor.
- `evaluate(X, Y, batch_size=128)` builds a feed dict and evaluates each
  collected train op's metric with the `Evaluator`. If the regression metric was
  disabled or `None`, there may be no useful metric to report.
- `save(model_file)` uses a TensorFlow `Saver`. The argument is a **checkpoint
  stem**, not a directory. TensorFlow writes sidecar files such as
  `<stem>.index`, `<stem>.meta`, and `<stem>.data-...`.
- `load(model_file, weights_only=False, **restore_options)` restores from the
  checkpoint stem. When `weights_only=True`, only trainable variables are
  restored; optimizer slots, moving averages, global step, and non-trainable
  helper variables are skipped.

Restore options accepted through `DNN.load(..., **optargs)` are passed to
`Trainer.restore`:

```python
model.load(stem,
           weights_only=True,
           variable_name_map=None,
           scope_for_restore=None,
           create_new_session=True,
           verbose=False)
```

See [checkpointing](checkpointing.md#restore-into-renamed-variable-scopes) for
scope-remapping patterns.

### Weights

```python
vars_ = tflearn.variables.get_layer_variables_by_name('dense1')
weights = model.get_weights(vars_[0])
model.set_weights(vars_[0], weights)

# Many layers also attach variables to the returned tensor:
weights = model.get_weights(dense_layer.W)
biases = model.get_weights(dense_layer.b)
```

Use weights APIs only after the model session has been initialized/restored.
If using `tflearn.variables.get_value(var)`, run it under the model session:

```python
with model.session.as_default():
    value = tflearn.variables.get_value(vars_[1])
```

## Feed Dictionary Name Resolution

TFLearn's `feed_dict_builder` converts user data into TensorFlow feed dicts.
Name resolution rules:

- For `input_data(shape=..., name='input')`, the TensorFlow placeholder is
  normally named `input/X:0`; dictionary key `'input'` resolves to that
  placeholder.
- If you supplied a custom placeholder named `input1`, the exact tensor name
  string `'input1:0'` also resolves.
- For `regression(..., name='target')`, the target placeholder is normally
  `target/Y:0`; dictionary key `'target'` resolves to it.
- Tensor keys bypass name lookup: `{placeholder_tensor: array}`.
- Unknown string keys raise an error like:
  `Feed dict asks for variable named 'non_existent' but no such variable is known to exist`.

For multi-input/multi-target list feeds, order is the order in
`tf.GraphKeys.INPUTS` and `tf.GraphKeys.TARGETS`, which is the creation order of
`input_data` and `regression`/target placeholders. In notebooks, repeated graph
construction cells can silently add extra placeholders to the default graph;
reset or isolate the graph before debugging list-order errors.

## Lower-Level Trainer, TrainOp, and Evaluator

Use these when training a custom TensorFlow graph instead of the high-level
`DNN` wrapper.

### TrainOp

Constructor signature:

```python
tflearn.TrainOp(loss,
                optimizer,
                metric=None,
                batch_size=64,
                ema=0.0,
                trainable_vars=None,
                shuffle=True,
                step_tensor=None,
                validation_monitors=None,
                validation_batch_size=None,
                name=None,
                graph=None)
```

Key points:

- `loss` must be a TensorFlow `Tensor`.
- `optimizer` must be a TensorFlow optimizer object, such as
  `tf.train.GradientDescentOptimizer(...)`, not a TFLearn optimizer name string.
  TFLearn string optimizers are handled by `tflearn.regression(...)`.
- `metric` is optional and can be any TensorFlow tensor that evaluates per batch.
- `trainable_vars` limits what variables are optimized; default is all
  trainable variables.
- `validation_monitors` are extra rank-1 tensors computed during validation and
  summarized to TensorBoard.
- `validation_batch_size` defaults to `batch_size` when omitted.

### Trainer

Common constructor pattern:

```python
trainer = tflearn.Trainer([train_op1, train_op2],
                          tensorboard_dir='/tmp/tflearn',
                          tensorboard_verbose=0,
                          checkpoint_path='/tmp/ckpts/model',
                          max_checkpoints=3)
```

Fit signature:

```python
trainer.fit(feed_dicts,
            n_epoch=10,
            val_feed_dicts=None,
            show_metric=False,
            snapshot_step=None,
            snapshot_epoch=True,
            shuffle_all=None,
            dprep_dict=None,
            daug_dict=None,
            excl_trainops=None,
            run_id=None,
            callbacks=[])
```

Feed rules:

- One optimizer: `feed_dicts={input_ph: X, target_ph: Y}`.
- Multiple optimizers: `feed_dicts=[dict_for_trainop1, dict_for_trainop2]`.
- Validation can mirror the feed structure or be a float split such as `0.1`.
- `excl_trainops=[train_op]` temporarily excludes one train op for the call.

`Trainer.save(model_file, global_step=None, use_val_saver=False)` and
`Trainer.restore(model_file, trainable_variable_only=False,
variable_name_map=None, scope_for_restore=None, create_new_session=True,
verbose=False)` are the underlying persistence operations used by `DNN`.

### Evaluator

```python
evaluator = tflearn.Evaluator([output_tensor], session=trainer.session)
pred = evaluator.predict({input_ph: X})
metrics = evaluator.evaluate({input_ph: X, target_ph: Y}, [metric_tensor], batch_size=128)
```

`Evaluator.predict` sets TFLearn training mode to false and applies any
registered data preprocessing for inputs before running tensors.

## Callbacks and TrainingState

Subclass `tflearn.callbacks.Callback` and pass an instance or list to
`DNN.fit(..., callbacks=...)` or `Trainer.fit(..., callbacks=...)`.

Callback methods:

```python
on_train_begin(training_state)
on_epoch_begin(training_state)
on_batch_begin(training_state)
on_sub_batch_begin(training_state)
on_sub_batch_end(training_state, train_index=0)
on_batch_end(training_state, snapshot=False)
on_epoch_end(training_state)
on_train_end(training_state)
```

Useful `training_state` fields include:

- `epoch`, `step`, `current_iter`, `step_time`
- `loss_value`, `acc_value`, `val_loss`, `val_acc`
- `global_loss`, `global_acc`, `best_accuracy`

TFLearn also installs internal callbacks during `fit`: `TermLogger` prints
progress and `ModelSaver` handles snapshot saves.

## TensorBoard Summaries

`tensorboard_verbose` controls automatic summaries built by `TrainOp`:

| Level | Summaries |
|---|---|
| `0` | Loss and metric only; fastest. |
| `1` | Loss/metric plus gradients. |
| `2` | Level 1 plus variable weights. |
| `3` | Level 2 plus activations and sparsity-style activation summaries; slowest but richest. |

At fit time, TFLearn prints:

```text
Run id: <run_id>
Log directory: <tensorboard_dir>
```

Event files are written under `<tensorboard_dir>/<run_id>`. Launch TensorBoard
against the base directory or the run directory:

```bash
tensorboard --logdir /tmp/tflearn_logs
```
