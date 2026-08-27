# Checkpointing, Weights, and Restore Mapping

This reference explains how TFLearn 0.5.0 saves and restores models through
TensorFlow 1.x `Saver` objects, how automatic snapshots relate to manual saves,
and how to restore weights when variable scopes changed.

## Checkpoint Stems vs Files

TFLearn `DNN.save(model_file)` and `DNN.load(model_file, ...)` expect a
**checkpoint stem**.

```python
stem = '/tmp/exp/model.tfl'
model.save(stem)
model.load(stem)
```

TensorFlow writes sidecar files next to the stem, for example:

```text
/tmp/exp/model.tfl.index
/tmp/exp/model.tfl.meta
/tmp/exp/model.tfl.data-00000-of-00001
/tmp/exp/checkpoint
```

Do not call `load('/tmp/exp/model.tfl.index')`. Load the stem
`'/tmp/exp/model.tfl'`.

When `Trainer.save` receives a relative path, it resolves it under the current
working directory. For reproducible agent workflows, use absolute paths or paths
inside an explicit experiment/temp directory.

## Manual Save/Load Workflow

```python
model.save('/tmp/exp/model.tfl')

# Rebuild the same graph architecture in a new graph.
restored = tflearn.DNN(net)
restored.load('/tmp/exp/model.tfl')
print(restored.predict(X[:2]))
```

Checklist:

- Same architecture and compatible variable names are present before `load`.
- The graph is fresh unless intentionally sharing variables/session.
- The checkpoint stem has `.index` and `.data-*` sidecar files.
- A prediction/evaluation after `load` matches expected shape and rough values.

## Automatic Snapshots During Fit

Automatic snapshots are controlled by `DNN` constructor paths plus `fit` options:

```python
model = tflearn.DNN(net,
                    checkpoint_path='/tmp/exp/auto/model.tfl.ckpt',
                    best_checkpoint_path='/tmp/exp/best/model-',
                    max_checkpoints=3,
                    best_val_accuracy=0.0)
model.fit(X, Y,
          validation_set=(valX, valY),
          show_metric=True,
          snapshot_epoch=True,
          snapshot_step=500,
          run_id='run_001')
```

Behavior:

- `checkpoint_path=None`: no regular auto-checkpoint is saved, even if snapshots
  occur for validation/logging.
- `snapshot_epoch=True`: `ModelSaver` saves at the end of each epoch using the
  training step as TensorFlow `global_step`, producing stems like
  `model.tfl.ckpt-17`.
- `snapshot_step=N`: saves when the global training step is divisible by `N`.
- `best_checkpoint_path`: if validation accuracy exists and improves beyond
  `best_val_accuracy`, TFLearn appends an integerized accuracy to the prefix and
  saves through a one-checkpoint validation saver.
- `max_checkpoints`: limits regular saver retention when TensorFlow writes new
  checkpoint states.

If both `snapshot_epoch=False` and `snapshot_step=None`, training can still run
but automatic checkpoint saves will not happen. Use `model.save(stem)` manually
when persistence is required.

## Weights-Only Restore

```python
model.load(stem, weights_only=True)
```

`weights_only=True` maps to `Trainer.restore(..., trainable_variable_only=True)`.
It restores only trainable variables. It intentionally skips non-trainable state
such as optimizer slots, moving averages, global step, and some helper variables.
Use it for transfer learning, loading subnet weights, or loading the same model
into multiple scoped copies. Avoid it when you need an exact resume of optimizer
state.

If a `regression(..., restore=False)` or `tflearn.variables.variable(...,
restore=False)` created exclude-restore entries, those variables are also
excluded from the standard restorer.

## Restore Into Renamed Variable Scopes

TFLearn exposes two restore-mapping tools through `DNN.load(..., **optargs)` and
`Trainer.restore(...)`.

### `scope_for_restore`

Use this when the current variables live under a new scope, but the checkpoint
was saved without that scope. TFLearn restores only current variables inside the
scope and strips the scope prefix to find names in the file.

```python
with tf.Graph().as_default():
    with tf.variable_scope('scopeA'):
        net = build_model()       # variables are named scopeA/...
    model = tflearn.DNN(net)
    model.load('/tmp/model1.tfl',
               scope_for_restore='scopeA',
               weights_only=True,
               verbose=True)
```

Conceptually, for a current variable named `scopeA/FullyConnected/W`, TFLearn
looks for `FullyConnected/W` in the checkpoint.

Use `create_new_session=False` when loading multiple scopes into the same graph
and session:

```python
combined.model.load(model1_stem,
                    scope_for_restore='scope1',
                    weights_only=True)
combined.model.load(model2_stem,
                    scope_for_restore='scope2',
                    weights_only=True,
                    create_new_session=False)
```

Without `create_new_session=False`, the second load creates a new session and
reinitializes variables, losing the first restore.

### `variable_name_map=(pattern, repl)`

Use a tuple to apply regular-expression substitution to each **current**
variable name to obtain the name to read from the checkpoint.

```python
with tf.Graph().as_default():
    with tf.variable_scope('scopeA'):
        net = build_model()
    model = tflearn.DNN(net)
    model.load('/tmp/model_scopeQ.tfl',
               variable_name_map=('scopeA', 'scopeQ'),
               verbose=True)
```

For a current variable `scopeA/dense1/W`, TFLearn asks the checkpoint for
`scopeQ/dense1/W`.

### `variable_name_map=function`

Use a function for custom inclusion/exclusion or complex renames. It receives
the current variable op name and returns the checkpoint variable name, or
`None` to skip that variable.

```python
def map_current_to_file(current_name):
    if not current_name.startswith('scopeA/'):
        return None
    return current_name.replace('scopeA/', 'scopeQ/', 1)

model.load('/tmp/model_scopeQ.tfl',
           variable_name_map=map_current_to_file,
           weights_only=True,
           verbose=True)
```

When `verbose=True`, TFLearn prints restore mappings such as:

```text
Restoring scopeA/dense1/W <- scopeQ/dense1/W
```

## Missing Variables and NotFoundError

A scope mismatch commonly raises `tf.errors.NotFoundError` because the current
variable name is not present in the checkpoint. Fix by choosing one of these:

1. Rebuild with the same scope names as the saved model.
2. Use `scope_for_restore='new_scope'` when the saved names are unscoped and the
   current graph is scoped.
3. Use `variable_name_map=('current_scope', 'saved_scope')` when both current and
   saved names have different scopes.
4. Use a mapping function to skip intentionally new variables and restore only a
   compatible subset.
5. Use `weights_only=True` when optimizer/non-trainable variables differ but
   trainable layer weights are compatible.

For deeper failure signals, see [troubleshooting](troubleshooting.md#restore-and-checkpoint-failures).

## Layer Variable Inspection and Editing

Retrieve by layer name:

```python
dense_vars = tflearn.variables.get_layer_variables_by_name('dense1')
W, b = dense_vars[0], dense_vars[1]
print(model.get_weights(W))
```

Retrieve from attached tensor attributes when available:

```python
dense = tflearn.fully_connected(input_layer, 64, name='dense2')
print(model.get_weights(dense.W))
model.set_weights(dense.b, new_bias_values)
```

Retrieve through a session:

```python
with model.session.as_default():
    value = tflearn.variables.get_value(dense.b)
```

Rules:

- Call these after `DNN` has initialized/restored its session.
- Shapes must match exactly for `set_weights`.
- If a layer name returns an empty list, inspect actual variable names:

```python
print([v.name for v in tflearn.variables.get_all_variables()])
```

## Checkpoint Hygiene for Agents

- Use a task-specific directory and clean it after temporary verification if the
  user did not request durable artifacts.
- Never write smoke checkpoints into the repository root by default. The bundled
  smoke script uses `tempfile` unless `--model-dir` is supplied.
- Record the checkpoint **stem** in outputs, not just the directory.
- For long runs, set both a stable `run_id` and a stable checkpoint stem.
- For restore tests, prove persistence with a prediction/evaluation after load.
