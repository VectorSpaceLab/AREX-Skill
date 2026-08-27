# Training, Evaluation, Prediction, and Debugging Workflows

These workflows are self-contained patterns for future agents to adapt without
reopening the original repository. They focus on training mechanics; choose
layers/data recipes from sibling sub-skills when needed.

## One-Input DNN Regression Smoke

Use this as the smallest shape-safe DNN pattern. The bundled script
[`../scripts/tiny_dnn_regression_smoke.py`](../scripts/tiny_dnn_regression_smoke.py)
implements a no-network version with command-line flags.

```python
import tensorflow.compat.v1 as tf
import tflearn

X = [3.3, 4.4, 5.5, 6.71, 6.93, 4.168, 9.779, 6.182]
Y = [1.7, 2.76, 2.09, 3.19, 1.694, 1.573, 3.366, 2.596]

with tf.Graph().as_default():
    input_ = tflearn.input_data(shape=[None], name='input')
    linear = tflearn.single_unit(input_)
    net = tflearn.regression(linear,
                             optimizer='sgd',
                             loss='mean_square',
                             metric='R2',
                             learning_rate=0.01,
                             name='target')
    model = tflearn.DNN(net, tensorboard_verbose=0)
    model.fit({'input': X}, {'target': Y},
              n_epoch=20,
              show_metric=True,
              snapshot_epoch=False,
              run_id='tiny_regression')
    print(model.predict([3.2, 3.3, 3.4]))
```

Validation steps:

- Fit prints a run id and log directory.
- `predict` returns a NumPy array with one prediction per input sample.
- `tf.get_collection(tf.GraphKeys.INPUTS)` contains the input placeholder.
- `tf.get_collection(tf.GraphKeys.TRAIN_OPS)` is non-empty after `regression`.

## Save, Load, and Re-Predict

Use explicit model stems under a writable experiment directory. A TFLearn
checkpoint stem is a file prefix, not a directory.

```python
import os
import tempfile
import tensorflow.compat.v1 as tf
import tflearn

X = [3.3, 4.4, 5.5, 6.71]
Y = [1.7, 2.76, 2.09, 3.19]
model_dir = tempfile.mkdtemp(prefix='tflearn-run-')
stem = os.path.join(model_dir, 'tiny_model.tflearn')

with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None], name='input')
    y = tflearn.single_unit(x)
    y = tflearn.regression(y, optimizer='sgd', loss='mean_square',
                           metric='R2', learning_rate=0.01, name='target')
    model = tflearn.DNN(y, tensorboard_verbose=0)
    model.fit({'input': X}, {'target': Y}, n_epoch=5, snapshot_epoch=False)
    before = model.predict([3.2])
    model.save(stem)
    assert os.path.exists(stem + '.index')

with tf.Graph().as_default():
    x = tflearn.input_data(shape=[None], name='input')
    y = tflearn.single_unit(x)
    y = tflearn.regression(y, optimizer='sgd', loss='mean_square',
                           metric='R2', learning_rate=0.01, name='target')
    restored = tflearn.DNN(y, tensorboard_verbose=0)
    restored.load(stem)
    after = restored.predict([3.2])
    print('before', before, 'after', after)
```

Validation steps:

- Use `stem` for `save` and `load`, not `stem + '.index'`.
- Rebuild the same graph architecture before `load`.
- Run at least one prediction or evaluation after loading.

For checkpoint details and scope mapping, see
[checkpointing](checkpointing.md).

## Multi-Input Fitting

When the graph has multiple `input_data` placeholders, prefer dictionaries with
names or tensors. Lists are allowed but are matched by creation order.

```python
import tensorflow.compat.v1 as tf
import tflearn

X1 = [[1.], [2.], [3.], [4.], [5.]]
X2 = [[6.], [7.], [8.], [9.], [10.]]
Y = [[14.], [18.], [22.], [26.], [30.]]

with tf.Graph().as_default():
    ph1 = tf.placeholder(tf.float32, (None, 1), name='input1')
    ph2 = tf.placeholder(tf.float32, (None, 1), name='input2')
    in1 = tflearn.input_data(placeholder=ph1)
    in2 = tflearn.input_data(placeholder=ph2)
    net = tflearn.merge([in1, in2], 'sum')
    net = tflearn.fully_connected(net, 1)
    net = tflearn.regression(net, loss='mean_square', optimizer='sgd',
                             learning_rate=0.01, name='target')
    model = tflearn.DNN(net)

    # Preferred: tensor keys are unambiguous.
    model.fit({ph1: X1, ph2: X2}, {'target': Y}, n_epoch=5, batch_size=1)

    # Also valid: exact placeholder names for custom placeholders.
    model.fit({'input1:0': X1, 'input2:0': X2}, {'target': Y},
              n_epoch=5, batch_size=1)

    # Valid but more fragile: creation-order list.
    model.fit([X1, X2], Y, n_epoch=5, batch_size=1)
```

If a dict key is wrong, TFLearn raises a feed-name error. Inspect names with:

```python
print([t.name for t in tf.get_collection(tf.GraphKeys.INPUTS)])
print([t.name for t in tf.get_collection(tf.GraphKeys.TARGETS)])
```

## Multi-Target / Multiple TrainOp Fitting

TFLearn permits more than one `regression(...)` call in one graph. `DNN.fit`
creates one feed dict and gives it to each collected train op unless you call
`Trainer` directly.

```python
import tensorflow.compat.v1 as tf
import tflearn

X = [[0., 0.], [0., 1.], [1., 0.], [1., 1.]]
Y_nand = [[1.], [1.], [1.], [0.]]
Y_or = [[0.], [1.], [1.], [1.]]

with tf.Graph().as_default():
    g = tflearn.input_data(shape=[None, 2], name='input')

    nand = tflearn.fully_connected(g, 8, activation='linear')
    nand = tflearn.fully_connected(nand, 1, activation='sigmoid')
    nand = tflearn.regression(nand, optimizer='sgd', learning_rate=2.,
                              loss='binary_crossentropy',
                              op_name='nand_train', name='nand_target')

    or_ = tflearn.fully_connected(g, 8, activation='linear')
    or_ = tflearn.fully_connected(or_, 1, activation='sigmoid')
    or_ = tflearn.regression(or_, optimizer='sgd', learning_rate=2.,
                             loss='binary_crossentropy',
                             op_name='or_train', name='or_target')

    out = tflearn.merge([nand, or_], mode='elemwise_mul')
    model = tflearn.DNN(out)

    model.fit({'input': X},
              {'nand_target': Y_nand, 'or_target': Y_or},
              n_epoch=100,
              snapshot_epoch=False)
```

Notes:

- If you pass target lists, order is target placeholder creation order.
- If two regressions intentionally share the same target placeholder, pass that
  placeholder explicitly to both `regression(..., placeholder=Y_in, name='Y')`;
  TFLearn avoids duplicate target collection entries.
- To train only one train op temporarily, retrieve train ops with
  `tf.get_collection_ref(tf.GraphKeys.TRAIN_OPS)` and pass `excl_trainops=[...]`.

## Validation and Snapshots

Use validation when you need validation loss/metric, best checkpoints, or
snapshot-time monitoring.

```python
model = tflearn.DNN(net,
                    tensorboard_dir='/tmp/tflearn_logs/',
                    checkpoint_path='/tmp/tflearn_ckpts/model.tfl.ckpt',
                    best_checkpoint_path='/tmp/tflearn_ckpts/best-model-',
                    max_checkpoints=3,
                    best_val_accuracy=0.0)

model.fit({'input': trainX}, {'target': trainY},
          validation_set=({'input': valX}, {'target': valY}),
          validation_batch_size=32,
          n_epoch=3,
          show_metric=True,
          snapshot_epoch=True,
          snapshot_step=500,
          run_id='experiment_001')
```

Behavior:

- End-of-epoch save: `snapshot_epoch=True` plus `checkpoint_path` saves
  `<checkpoint_path>-<global_step>` at epoch end.
- Step save: `snapshot_step=500` plus `checkpoint_path` saves every 500 global
  training steps.
- Best save: `best_checkpoint_path` saves when validation accuracy is not
  `None` and improves beyond `best_val_accuracy`; the validation accuracy is
  appended to the stem.
- Validation split: `validation_set=0.1` shuffles sample indices and holds out
  10% from the same feed data.
- Memory tuning: `validation_batch_size` can be smaller than training
  `batch_size`.

## TensorBoard Workflow

```python
model = tflearn.DNN(net,
                    tensorboard_verbose=2,
                    tensorboard_dir='/tmp/tflearn_logs/')
model.fit(X, Y, n_epoch=2, run_id='run_a')
```

Then launch:

```bash
tensorboard --logdir /tmp/tflearn_logs
```

If a user cannot find event files:

1. Read the printed `Log directory: ...` line.
2. Check for a subdirectory named by `run_id` or a generated id.
3. Set `tensorboard_verbose=0` for fast minimal logging, or `2`/`3` only when
   gradients/weights/activations are needed.

## Custom Trainer Workflow

Use `Trainer` when the graph is not expressed through TFLearn `regression`, or
when each optimizer needs a distinct feed dictionary.

```python
import tensorflow.compat.v1 as tf
import tflearn
from tflearn.helpers.trainer import TrainOp, Trainer
from tflearn.helpers.evaluator import Evaluator

with tf.Graph().as_default():
    x = tf.placeholder(tf.float32, [None, 1], name='x')
    y_true = tf.placeholder(tf.float32, [None, 1], name='y')
    w = tf.Variable([[0.0]], name='w')
    b = tf.Variable([0.0], name='b')
    y_pred = tf.matmul(x, w) + b
    loss = tf.reduce_mean(tf.square(y_pred - y_true))
    optimizer = tf.train.GradientDescentOptimizer(0.01)

    train_op = TrainOp(loss=loss,
                       optimizer=optimizer,
                       metric=None,
                       batch_size=4,
                       name='linear_train')
    trainer = Trainer(train_op,
                      tensorboard_dir='/tmp/tflearn_trainer_logs/',
                      checkpoint_path='/tmp/tflearn_trainer_ckpts/model')
    trainer.fit({x: [[1.], [2.], [3.]], y_true: [[2.], [4.], [6.]]},
                n_epoch=10,
                snapshot_epoch=False,
                run_id='custom_linear')

    evaluator = Evaluator([y_pred], session=trainer.session)
    print(evaluator.predict({x: [[4.]]}))
```

Rules:

- Pass TensorFlow placeholders as feed keys unless you deliberately add them to
  TFLearn collections and use name lookup.
- For multiple train ops, pass `Trainer([op1, op2])` and a list of feed dicts in
  the same order: `trainer.fit([{...}, {...}], val_feed_dicts=[{...}, {...}])`.
- `Trainer` creates and owns a session unless you pass an initialized one.

## Callbacks and TrainingState

A callback can monitor, stop external jobs, or emit custom logs. It should not
mutate feed dict structure during training.

```python
import tflearn

class PrintEveryEpoch(tflearn.callbacks.Callback):
    def on_epoch_end(self, training_state):
        print('epoch', training_state.epoch,
              'loss', training_state.global_loss,
              'val_acc', training_state.val_acc)

model.fit(X, Y, n_epoch=3, callbacks=[PrintEveryEpoch()])
```

Callback lifecycle methods are listed in [api-reference](api-reference.md#callbacks-and-trainingstate).
`on_batch_end(training_state, snapshot)` receives `snapshot=True` when the
current step/epoch triggered snapshot evaluation/saving.

## Debug Before Training

Before a long run, run these checks:

```python
print('inputs:', [t.name for t in tf.get_collection(tf.GraphKeys.INPUTS)])
print('targets:', [t.name for t in tf.get_collection(tf.GraphKeys.TARGETS)])
print('train ops:', [getattr(op, 'name', None) for op in tf.get_collection(tf.GraphKeys.TRAIN_OPS)])
```

Expected signals:

- Inputs list is non-empty before `tflearn.DNN(net)`.
- Targets/train ops are non-empty before `model.fit(...)`.
- Names match dictionary keys. For an `input_data(name='input')`, key `'input'`
  maps to placeholder `input/X:0`; for `regression(name='target')`, key
  `'target'` maps to target `target/Y:0`.
- In notebooks, duplicate placeholders after rerunning graph-building cells are
  a sign to reset the graph.
