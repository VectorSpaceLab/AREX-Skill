# Layers and Ops Workflows

Use these workflows to build and validate TFLearn graph components without reopening the original repository. They intentionally stop at graph construction and train-op wiring. Actual `DNN.fit`, checkpoint persistence, callbacks, and long-running examples belong to `training-and-persistence`.

## Workflow 1: Build a minimal supervised graph

This is the safest starting pattern for a single-input, single-output classifier/regressor.

```python
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import tflearn

with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None, 4], name='features')
    net = tflearn.fully_connected(x, 8, activation='relu', name='dense1')
    net = tflearn.dropout(net, 0.8, name='dropout1')  # keep_prob, not drop rate
    net = tflearn.fully_connected(net, 2, activation='softmax', name='class_head')
    net = tflearn.regression(net, optimizer='sgd', learning_rate=0.05,
                             loss='categorical_crossentropy',
                             metric='accuracy', name='labels')

    print('inputs:', [t.name for t in tf.get_collection(tf.GraphKeys.INPUTS)])
    print('targets:', [t.name for t in tf.get_collection(tf.GraphKeys.TARGETS)])
    print('train ops:', len(tf.get_collection(tf.GraphKeys.TRAIN_OPS)))
    print('dense vars:', [v.name for v in tflearn.get_layer_variables_by_name('dense1')])
```

Expected construction signals:

- `INPUTS` contains one placeholder, usually `features/X:0`.
- `TARGETS` contains one placeholder, usually `labels/Y:0`.
- `TRAIN_OPS` contains one `TrainOp` created by `regression`.
- `tflearn.get_layer_variables_by_name('dense1')` returns the dense `W` and `b` variables.

If the output layer uses `activation='softmax'`, pair it with `loss='categorical_crossentropy'`. If you want TensorFlow to apply softmax inside the loss, make the output layer `activation='linear'` and use `loss='softmax_categorical_crossentropy'`.

## Workflow 2: Run the bundled graph smoke script

Use the script when checking whether the active Python environment can import TFLearn and construct a small graph.

```bash
python scripts/layer_graph_smoke.py --help
python scripts/layer_graph_smoke.py
python scripts/layer_graph_smoke.py --skip-session-run
```

The script is safe and no-network. It builds an input layer, two dense branches, a merge, dropout, a classification head, and `regression`. It prints collection counts and, unless skipped, performs one TensorFlow session evaluation without training.

Expected output fragments:

- `collection INPUTS: 1`
- `collection TARGETS: 1`
- `collection TRAIN_OPS: 1`
- `prediction_shape: (2, 2)` when the session run is enabled
- `OK layer graph smoke completed`

If import fails in a modern TensorFlow 2 environment, use the compatibility troubleshooting table before changing graph code.

## Workflow 3: Diagnose a layer name and collection issue

Use this when a future training task reports missing inputs, missing targets, unknown feed names, or empty train ops.

```python
with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None, 3], name='X_in')
    out = tflearn.fully_connected(x, 1, activation='linear', name='score')
    out = tflearn.regression(out, optimizer='adam', loss='mean_square', name='Y_out')

    assert len(tf.get_collection(tf.GraphKeys.INPUTS)) == 1
    assert len(tf.get_collection(tf.GraphKeys.TARGETS)) == 1
    assert len(tf.get_collection(tf.GraphKeys.TRAIN_OPS)) == 1

    print(tflearn.variables.get_inputs_placeholder_by_name('X_in'))
    print(tflearn.variables.get_targets_placeholder_by_name('Y_out'))
    print(tflearn.get_layer_by_name('score'))
```

Guidance:

- Use `input_data(name='X_in')` if downstream code will feed `{'X_in': X}`.
- Use `regression(name='Y_out')` if downstream code will feed `{'Y_out': Y}`.
- If you bypass `input_data` and create `tf.placeholder` manually, add it to `tf.GraphKeys.INPUTS` or name-based feed helpers will not find it:

  ```python
  x = tf.placeholder(tf.float32, shape=[None, 3], name='raw_x')
  tf.add_to_collection(tf.GraphKeys.INPUTS, x)
  ```

## Workflow 4: Build a multi-branch merge graph with two heads

This pattern is useful for multi-task graphs and for the logical-operator example style. It creates two training heads and optionally merges their predictions.

```python
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import tflearn

with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None, 2], name='logic_input')

    nand = tflearn.fully_connected(x, 16, activation='linear', name='nand_fc1')
    nand = tflearn.fully_connected(nand, 1, activation='sigmoid', name='nand_out')
    nand = tflearn.regression(nand, optimizer='sgd', learning_rate=0.5,
                              loss='binary_crossentropy', metric=None,
                              op_name='nand_train', name='nand_target')

    or_head = tflearn.fully_connected(x, 16, activation='linear', name='or_fc1')
    or_head = tflearn.fully_connected(or_head, 1, activation='sigmoid', name='or_out')
    or_head = tflearn.regression(or_head, optimizer='sgd', learning_rate=0.5,
                                 loss='binary_crossentropy', metric=None,
                                 op_name='or_train', name='or_target')

    xor_like = tflearn.merge([nand, or_head], mode='elemwise_mul', name='xor_merge')

    targets = tf.get_collection(tf.GraphKeys.TARGETS)
    train_ops = tf.get_collection(tf.GraphKeys.TRAIN_OPS)
    print([t.name for t in targets])      # ['nand_target/Y:0', 'or_target/Y:0']
    print([op.name for op in train_ops])  # train op metadata names
```

Target-feed guidance for later training:

- With high-level `DNN.fit`, pass target arrays in the same order as the target placeholders were created, for example `[Y_nand, Y_or]`.
- With named dict feeds, use the `regression(name=...)` values: `{'nand_target': Y_nand, 'or_target': Y_or}` if handing the graph to TFLearn feed helpers.
- With raw TensorFlow `Session.run`, feed the actual placeholder tensors from `tf.get_collection(tf.GraphKeys.TARGETS)`.
- If both heads intentionally share one target placeholder, create that placeholder once and pass it as `placeholder=shared_y` to each `regression`; TFLearn avoids adding the same placeholder twice to `TARGETS`.

Merge-choice rules:

- Use `elemwise_sum` or `elemwise_mul` when branch tensors have identical shapes.
- Use `concat` when you want to preserve features from branches and dimensions match except along `axis`.
- Use `merge_outputs` only when separate outputs should be concatenated as one prediction tensor.

## Workflow 5: Integrate TFLearn ops into a raw TensorFlow graph

TFLearn activations, objectives, metrics, optimizers, variables, and summaries can be used without TFLearn layer wrappers.

```python
with tf.Graph().as_default():
    x = tf.placeholder(tf.float32, shape=[None, 4], name='x')
    y = tf.placeholder(tf.float32, shape=[None, 2], name='y')
    tf.add_to_collection(tf.GraphKeys.INPUTS, x)
    tf.add_to_collection(tf.GraphKeys.TARGETS, y)

    w = tflearn.variable('W', shape=[4, 2], initializer='truncated_normal', regularizer='L2')
    b = tflearn.variable('b', shape=[2], initializer='zeros')
    logits = tf.matmul(x, w) + b
    preds = tflearn.softmax(logits)

    loss = tflearn.softmax_categorical_crossentropy(logits, y)
    acc = tflearn.metrics.accuracy_op(preds, y)
    tflearn.summaries.monitor_activation(preds)

    opt = tflearn.SGD(learning_rate=0.1).get_tensor()
    trainop = tflearn.TrainOp(loss=loss, optimizer=opt, metric=acc, batch_size=32)
    tf.add_to_collection(tf.GraphKeys.TRAIN_OPS, trainop)
```

Notes:

- `TrainOp` construction is enough for graph metadata. Training orchestration with `Trainer` is handled by `training-and-persistence`.
- If an optimizer has learning-rate decay, build it with a step tensor before calling `get_tensor()`.
- Add raw placeholders to `INPUTS`/`TARGETS` if future code will use TFLearn feed builders or `Trainer`/`DNN` style discovery.

## Workflow 6: Select layer families by tensor rank

Use rank-driven selection before choosing architecture details.

### Dense/tabular graph

```python
x = tflearn.input_data(shape=[None, n_features])
h = tflearn.fully_connected(x, 64, activation='relu')
h = tflearn.fully_connected(h, 32, activation='relu')
y = tflearn.fully_connected(h, n_outputs, activation='linear')
y = tflearn.regression(y, loss='mean_square', metric=None)
```

### Image-like convolution graph

```python
x = tflearn.input_data(shape=[None, height, width, channels])
h = tflearn.conv_2d(x, 32, 3, activation='relu', padding='same')
h = tflearn.max_pool_2d(h, 2)
h = tflearn.batch_normalization(h)
h = tflearn.fully_connected(h, n_classes, activation='softmax')
y = tflearn.regression(h, loss='categorical_crossentropy')
```

Validate rank before conv layers:

```python
assert len(h.get_shape().as_list()) == 4
```

### Sequence embedding + RNN graph

```python
x = tflearn.input_data(shape=[None, timesteps], dtype=tf.float32, name='token_ids')
h = tflearn.embedding(x, input_dim=vocab_size, output_dim=embedding_dim)
h = tflearn.lstm(h, 64, dynamic=True, dropout=(0.8, 0.8))
y = tflearn.fully_connected(h, n_classes, activation='softmax')
y = tflearn.regression(y, loss='categorical_crossentropy')
```

Sequence assumptions:

- `embedding` expects rank 2 ids and casts them to `int32`.
- `dynamic=True` detects sequence length by treating zero-valued padded timesteps as padding. Use post-padding with zeros.
- Recurrent wrappers rely on TensorFlow v1 recurrent internals. If import or construction fails with missing `tensorflow.python.util.nest.is_sequence` or missing `tf.contrib`, use the compatibility fixes in troubleshooting.

## Workflow 7: Reuse scopes and inspect variables

Use `scope` and `reuse` for intentional weight sharing. The first layer call creates variables; the second call reuses them.

```python
with tf.Graph().as_default():
    x1 = tflearn.input_data(shape=[None, 4], name='view1')
    x2 = tflearn.input_data(shape=[None, 4], name='view2')

    h1 = tflearn.fully_connected(x1, 8, activation='relu', scope='shared_fc')
    h2 = tflearn.fully_connected(x2, 8, activation='relu', scope='shared_fc', reuse=True)

    vars_by_name = tflearn.get_layer_variables_by_name('shared_fc')
    vars_by_scope = tflearn.get_layer_variables_by_scope('shared_fc')
    print([v.name for v in vars_by_name])
    print([v.name for v in vars_by_scope])
```

Failure rules:

- If `reuse=True` is set before variables exist, TensorFlow raises a missing-variable reuse error.
- If `reuse=False`/default is used for an already-created scope, TensorFlow raises an already-exists error.
- `scope` controls variable names and reuse; `name` controls default layer naming when `scope` is not supplied.

## Workflow 8: Add summaries at graph construction time

Use TFLearn summaries when a custom graph should expose activation, variable, or loss summaries to a later training workflow.

```python
with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None, 4])
    h = tflearn.fully_connected(x, 8, activation='relu', name='hidden')
    tflearn.summaries.monitor_activation(h)

    y = tflearn.fully_connected(h, 2, activation='softmax')
    y = tflearn.regression(y, loss='categorical_crossentropy')

    activations = tf.get_collection(tf.GraphKeys.ACTIVATIONS)
    act_summaries = tflearn.summaries.add_activations_summary(
        activations, collection_key='custom_summaries')
    print('activation summaries:', len(act_summaries))
```

Keep summary creation separate from TensorBoard execution. TensorBoard directory choices and training-time summary execution belong to `training-and-persistence`.

## Workflow 9: Validate operation registry names before blaming TensorFlow

When a string identifier fails, test it directly against the relevant registry.

```python
for activation_name in ['relu', 'leaky_relu', 'not_an_activation']:
    try:
        fn = tflearn.activations.get(activation_name)
        print(activation_name, '->', fn)
    except Exception as exc:
        print(activation_name, 'FAILED:', exc)

for loss_name in ['categorical_crossentropy', 'mean_square', 'not_a_loss']:
    try:
        fn = tflearn.objectives.get(loss_name)
        print(loss_name, '->', fn)
    except Exception as exc:
        print(loss_name, 'FAILED:', exc)
```

Use the API reference tables for valid names. If a valid historical name still fails, inspect TensorFlow compatibility; some functions depend on TF1 contrib or TensorFlow v1 internals.

## Handoff checks before leaving this sub-skill

Before handing a constructed graph to training/data/recipe sub-skills, record:

- Input placeholders: names, shapes, dtypes, and whether they came from `input_data` or raw TensorFlow placeholders.
- Target placeholders: order and names from `tf.GraphKeys.TARGETS`.
- Output tensors: names and shapes, especially after merge or multi-head construction.
- Train ops: count from `tf.GraphKeys.TRAIN_OPS`, optimizer/loss/metric choices, and any `trainable_vars` restrictions.
- Variable scopes: intentional reuse scopes and restore exclusions.
- Data assumptions: only shape/dtype/preprocessing attachment points; defer actual data loading/preprocessing to `data-input-pipelines`.
