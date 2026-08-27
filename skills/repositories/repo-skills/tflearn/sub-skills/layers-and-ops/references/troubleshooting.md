# Layers and Ops Troubleshooting

Use this guide for graph-construction failures, layer/operation misuse, and TFLearn TensorFlow-v1 compatibility issues. For dataset loading/preprocessing, route to `data-input-pipelines`. For `.fit`, checkpoint save/load, callbacks, or TensorBoard execution, route to `training-and-persistence`.

## Fast diagnosis table

| Symptom / signal | Likely cause | Fix |
|---|---|---|
| `Either a shape or placeholder argument is required...` from `input_data` | Called `tflearn.input_data()` without `shape` or `placeholder`. | Pass `shape=[None, ...]` or an existing placeholder: `tflearn.input_data(placeholder=x, name='...')`. |
| `Incoming Tensor shape must be at least 2-D` | `fully_connected`/`flatten` received scalar or rank-1 tensor. | Reshape or define input as `[None, features]`, not `[features]` or `[]`. |
| `Incoming Tensor shape must be 4-D` from `conv_2d`/pooling | Image tensor missing batch/channel dimension or was flattened too early. | Use `[None, height, width, channels]` or `tflearn.reshape(x, [-1, h, w, c])` before 2D conv. |
| `Incoming Tensor shape must be 2-D` from `embedding` | Input ids have wrong rank. | Use `input_data(shape=[None, timesteps])`; pad sequences to fixed timesteps. |
| `Input dim should be at least 3.` from RNN | Recurrent layer received rank <3. | Feed embeddings or sequence features shaped `[batch, timesteps, features]`. |
| `Invalid activation: ...`, `Invalid objective: ...`, `Invalid metrics: ...`, `Invalid optimizer: ...` | Unknown registry string or typo. | Use names in [api-reference.md](api-reference.md), or pass a callable/class instance. Test with `tflearn.activations.get(name)` etc. |
| `Unknown merge mode` | `tflearn.merge` mode not in the supported mode list. | Use `concat`, `elemwise_sum`, `elemwise_mul`, `sum`, `mean`, `prod`, `max`, `min`, `and`, or `or`. |
| `Merge required 2 or more tensors.` | `tflearn.merge` received fewer than two tensors. | Use the tensor directly, or pass at least two branch tensors. |
| TensorFlow concat/add shape error in `merge` | Branch tensors are not shape-compatible for the selected merge mode. | Print `tensor.get_shape().as_list()` for each branch; use `concat` only when non-axis dims match and elementwise modes only when all dims match. |
| `n_classes is required when using to_one_hot` | `regression(to_one_hot=True)` omitted `n_classes`. | Add `n_classes=<class_count>` or one-hot encode targets outside `regression`. |
| Empty `tf.GraphKeys.TRAIN_OPS` | No `tflearn.regression` call, or graph was reset after building. | Call `regression` on each trainable head after output construction; validate collection count in the same graph. |
| Empty `tf.GraphKeys.INPUTS` | Used raw placeholders without `input_data`. | Prefer `input_data`; otherwise call `tf.add_to_collection(tf.GraphKeys.INPUTS, x)`. |
| Empty `tf.GraphKeys.TARGETS` | Did not call `regression`, used `placeholder=None`, or graph mismatch. | Use `regression(..., placeholder='default')` or add explicit target placeholder to `TARGETS`. |
| Feed helper says unknown variable name | Dict key does not match `input_data(name=...)` or `regression(name=...)`, or placeholder not in collection. | Print collections and use the layer names, or feed placeholders directly. |
| `Variable ... already exists` | Re-created a scoped layer in the same graph without `reuse=True` or graph reset. | Use `with tf.Graph().as_default()`, `tf.reset_default_graph()`, unique scopes, or explicit `reuse=True` for intended sharing. |
| `Variable ... does not exist, disallowed. Did you mean to set reuse=None or reuse=False?` | Set `reuse=True` before variables were created. | First build the layer with `reuse=False`/default; then build shared calls with `reuse=True`. |
| Dropout/batch norm behaves the same in train and test | TFLearn `is_training` mode is not set or variables not initialized in manual session workflow. | Initialize variables; use `tflearn.is_training(True, session=sess)` for train-mode checks and `False` for prediction checks. `DNN`/`Trainer` handle this for normal training. |
| Import fails with `tensorflow.python.util.nest.is_sequence` missing | Modern TensorFlow removed an internal API used by TFLearn recurrent code. | Use the verified TF1-style runtime (TensorFlow 1.15.x with Python 3.7-era deps) or refresh the code for TF2 compatibility outside this skill. |
| Import fails with protobuf descriptor errors | TensorFlow 1.15 with protobuf 4.x. | Use protobuf 3.20.x with TensorFlow 1.15.x. |
| `tf.contrib` / xavier / variance scaling errors | TF2 or stripped TensorFlow install lacks TF1 contrib initializers. | Use TensorFlow 1.15.x, or avoid `xavier`/`variance_scaling` and use `truncated_normal`, `uniform_scaling`, or explicit TensorFlow initializers. |
| GPU not used or device placement differs | CPU environment is valid; GPU is optional/unverified for this sub-skill. | Use `tflearn.init_graph(log_device=True, soft_placement=True)` for placement logs; do not require CUDA unless the broader task is performance-focused. |

## Shape/rank debugging procedure

1. Print the static shape immediately before the failing layer:

   ```python
   print('before conv:', net.get_shape().as_list())
   ```

2. Match the layer family to rank:

   - Dense/core: `fully_connected`, `flatten`, `highway` need rank >=2.
   - 1D conv/pool: rank 3 `[batch, width, channels]`.
   - 2D conv/pool/norm example: rank 4 `[batch, height, width, channels]`.
   - 3D conv/pool: rank 5 `[batch, depth, height, width, channels]`.
   - Embedding: rank 2 `[batch, ids]`.
   - RNN: rank >=3 `[batch, timesteps, features]` or a list of per-timestep tensors.

3. If the input data is flat but a conv layer is required, reshape before convolution:

   ```python
   x = tflearn.input_data(shape=[None, 784])
   net = tflearn.reshape(x, [-1, 28, 28, 1])
   net = tflearn.conv_2d(net, 32, 3, activation='relu')
   ```

4. If a dense layer follows conv/recurrent outputs, `fully_connected` can flatten rank >2 automatically. Explicit `flatten` is still useful for debugging.

5. For dynamic sequence RNNs, zero-padding affects computed sequence length. A real zero timestep is treated as padding; if zero is a valid timestep value, provide a different representation or avoid `dynamic=True`.

## Registry-name debugging

TFLearn resolves strings through module registries. The error may be from a misspelled name rather than from TensorFlow itself.

```python
checks = [
    ('activation', tflearn.activations.get, 'relu'),
    ('loss', tflearn.objectives.get, 'categorical_crossentropy'),
    ('metric', tflearn.metrics.get, 'Accuracy'),
    ('optimizer', tflearn.optimizers.get, 'adam'),
    ('initializer', tflearn.initializations.get, 'truncated_normal'),
    ('regularizer', tflearn.regularizers.get, 'L2'),
]
for kind, getter, name in checks:
    try:
        print(kind, name, '->', getter(name))
    except Exception as exc:
        print(kind, name, 'FAILED:', exc)
```

Rules of thumb:

- Activations are usually lowercase: `relu`, `leaky_relu`, `softmax`.
- Objectives are lowercase function names: `categorical_crossentropy`, `mean_square`.
- Optimizer class aliases are mostly lowercase: `adam`, `sgd`, `rmsprop`; class names also exist in module globals.
- Regularizers are uppercase in source: `L1`, `L2`. Prefer exact case.
- Metrics include classes such as `Accuracy`, `Top_k`, `R2`; for custom parameters, pass an instance: `tflearn.metrics.Top_k(k=5)`.

## `regression` and train-op problems

`regression` returns the incoming tensor while adding target placeholders and `TrainOp` objects. Do not expect it to change predictions.

### Missing target placeholder

```python
net = tflearn.fully_connected(x, 1)
net = tflearn.regression(net, placeholder=None, loss='mean_square')
print(tf.get_collection(tf.GraphKeys.TARGETS))  # []
```

`placeholder=None` is only for special cases where no target placeholder is required. Most supervised models should use the default placeholder or pass an explicit placeholder.

### Duplicate or shared placeholders

If two heads share the same explicit target placeholder, TFLearn only stores it once in `TARGETS`:

```python
with tf.name_scope('shared_target'):
    y = tf.placeholder(tf.float32, [None, 1], name='Y')
tflearn.regression(head1, placeholder=y, op_name='head1')
tflearn.regression(head2, placeholder=y, op_name='head2')
assert len(tf.get_collection(tf.GraphKeys.TARGETS)) == 1
```

If heads need different targets, let `regression` create different placeholders and give each a clear `name`.

### Invalid loss/metric shape pairing

- `categorical_crossentropy`: predictions and targets must have the same `[batch, classes]` shape and target rows should be one-hot/probability distributions.
- `softmax_categorical_crossentropy`: prediction tensor should be logits, not softmax probabilities.
- `binary_crossentropy`: prediction and target shapes must match; consider a linear/logit output for strict TensorFlow semantics.
- `metric='default'` maps to accuracy for classification shapes. For linear regression or incompatible shapes, use `metric=None` or an explicit metric.

## TensorFlow v1 graph/session behavior

TFLearn is not eager-first. The following pattern is reliable for manual graph checks:

```python
with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None, 2])
    y = tflearn.fully_connected(x, 1)

    init = tf.global_variables_initializer()
    with tf.Session() as sess:
        sess.run(init)
        tflearn.is_training(False, session=sess)
        value = sess.run(y, feed_dict={x: [[0.0, 1.0]]})
```

Important details:

- Importing TFLearn creates an `is_training` variable in the current default graph. If graph lifecycle is confusing in notebooks, reset the graph and import/build consistently.
- Variables must be initialized before running dropout, batch norm, PReLU, dense, conv, optimizers, or `is_training` assignment ops.
- Build and run tensors in the same graph/session. A tensor from an old graph cannot be fed into a new default graph.
- Prefer wrapping small tests in `with tf.Graph().as_default():` to avoid variable name collisions.

## Scope and reuse issues

TFLearn layers use `tf.variable_scope(scope, default_name=name, reuse=reuse)`. That means `scope` is the strongest control for variable names.

Correct weight sharing:

```python
h1 = tflearn.fully_connected(x1, 8, scope='shared')
h2 = tflearn.fully_connected(x2, 8, scope='shared', reuse=True)
```

Common mistakes:

- Using the same `scope` twice without `reuse=True` creates an already-exists error.
- Using `reuse=True` on the first call creates a missing-variable error.
- Changing `n_units`, input rank, or initializer shape while reusing a scope is invalid; reused variables must have compatible shapes.
- `name='dense'` is not the same as `scope='dense'` when both are supplied. Lookup by layer variables usually follows the resolved scope name.

## Recurrent/contrib compatibility

Recurrent layers and some initializers are the most TensorFlow-version-sensitive parts of this sub-skill.

Signals:

- Import error involving `tensorflow.python.util.nest.is_sequence`.
- Import/construction error involving `tensorflow.contrib.rnn` or `tensorflow.contrib.layers`.
- Runtime warnings/errors from old `static_rnn`, `static_bidirectional_rnn`, or contrib initializers.

Fix order:

1. Prefer the verified TF1-style runtime: Python 3.7-era environment, TensorFlow 1.15.x, protobuf 3.20.x.
2. If the task does not require RNNs, avoid importing/constructing recurrent wrappers in a modern runtime and use dense/conv workflows only.
3. For initializers, replace `xavier`/`variance_scaling` with `truncated_normal`, `uniform_scaling`, or an explicit TensorFlow initializer when TF contrib is unavailable.
4. Do not claim TF2-native compatibility for recurrent layers unless separately ported and verified.

## Optional GPU/device expectations

CPU graph construction is the verified baseline. GPU availability is optional for speed and larger models.

Use this only to inspect placement behavior:

```python
cfg = tflearn.init_graph(log_device=True, gpu_memory_fraction=0.0, soft_placement=True)
```

Guidance:

- `soft_placement=True` lets TensorFlow place unsupported GPU ops on CPU.
- Embedding variables are explicitly placed on CPU in TFLearn's embedding layer.
- A CPU-only TensorFlow wheel can build and run the graph smoke script.
- Do not block a graph-construction task because CUDA is unavailable unless the user explicitly asked for GPU placement/performance verification.

## Known compatibility gaps

- Modern Python 3.13 + TensorFlow 2.21 import is known to fail for this checkout because TensorFlow removed `tensorflow.python.util.nest.is_sequence`.
- TensorFlow 1.15.5 with protobuf 4.x is known to fail with descriptor-construction errors; protobuf 3.20.x is the compatible line.
- Some newer activation functions in the registry may depend on TensorFlow symbols present in later versions, while the package as a whole depends on TF1 internals. Verify those functions individually if they are critical.
- CUDA was not selected as a required backend for this sub-skill; treat GPU behavior as unverified beyond standard TensorFlow device placement.
