# Tensorpack training workflows

Use these workflows to design Tensorpack training code without reopening source
examples. For signatures, see [api-reference.md](api-reference.md). For example
families and dependency limits, see [example-recipes.md](example-recipes.md).

## Minimal ModelDesc + TrainConfig quickstart

This is the standard path for single-cost gradient optimization.

```python
import os
from tensorpack import tfv1 as tf
from tensorpack import (
    ModelDesc, TrainConfig, SimpleTrainer, launch_train_with_config,
    Conv2D, FullyConnected, MaxPooling, argscope,
    ModelSaver, InferenceRunner, ScalarStats, ScheduledHyperParamSetter)
from tensorpack.dataflow import BatchData, FakeData
from tensorpack.tfutils import summary
from tensorpack.utils import logger

class Model(ModelDesc):
    def inputs(self):
        return [tf.TensorSpec((None, 28, 28, 1), tf.float32, 'image'),
                tf.TensorSpec((None,), tf.int32, 'label')]

    def build_graph(self, image, label):
        image = tf.cast(image, tf.float32)
        with argscope(Conv2D, kernel_size=3, activation=tf.nn.relu):
            net = Conv2D('conv0', image, 16)
            net = MaxPooling('pool0', net, 2)
            net = Conv2D('conv1', net, 32)
        logits = FullyConnected('logits', net, 10, activation=tf.identity)
        loss = tf.nn.sparse_softmax_cross_entropy_with_logits(
            logits=logits, labels=label)
        loss = tf.reduce_mean(loss, name='cross_entropy')
        pred = tf.argmax(logits, axis=1, output_type=tf.int32, name='prediction')
        train_error = tf.reduce_mean(tf.cast(tf.not_equal(pred, label), tf.float32),
                                     name='train_error')
        summary.add_moving_summary(loss, train_error)
        return tf.identity(loss, name='total_cost')

    def optimizer(self):
        lr = tf.get_variable('learning_rate', initializer=1e-3, trainable=False)
        return tf.train.AdamOptimizer(lr)

def data(size=128):
    ds = FakeData([[28, 28, 1], [1]], size, random=False,
                  dtype=['float32', 'int32'], domain=[(0, 1), (0, 10)])
    ds = BatchData(ds, 16)
    return ds

if __name__ == '__main__':
    tf.disable_eager_execution()
    logger.set_logger_dir('train_log/example', action='k')
    train = data()
    valid = data(32)
    config = TrainConfig(
        model=Model(),
        dataflow=train,
        callbacks=[
            ModelSaver(),
            InferenceRunner(valid, [ScalarStats('total_cost')]),
            ScheduledHyperParamSetter('learning_rate', [(1, 1e-3), (3, 1e-4)]),
        ],
        steps_per_epoch=len(train),
        max_epoch=3)
    launch_train_with_config(config, SimpleTrainer())
```

For a bundled safe helper with fake data and command-line flags, use
[../scripts/minimal_training_smoke.py](../scripts/minimal_training_smoke.py).

### Decisions to make before writing code

- **Inputs:** list every tensor with shape, dtype, and name in `inputs()`.
- **Input source:** use `dataflow=...` for a Tensorpack `DataFlow`, or `data=...`
  for an `InputSource`. Route detailed DataFlow performance and construction to
  `../dataflow/SKILL.md`.
- **Cost:** `build_graph()` must return the final scalar cost for `ModelDesc`.
- **Regularization:** Tensorpack warns if regularization losses are created but
  not consumed. Add regularization explicitly into the returned cost.
- **Summaries:** use `summary.add_moving_summary` for noisy step-dependent
  scalars and `summary.add_param_summary` for variable summaries.
- **Learning-rate schedule:** if using `ScheduledHyperParamSetter`, create a
  non-trainable variable with a stable name, commonly `learning_rate`.
- **Checkpointing:** use `ModelSaver()` for periodic checkpoints and
  `SmartInit(...)` or `AutoResumeTrainConfig` for loading/resume.

## TrainConfig deep pattern

`TrainConfig` is only a container. It does not train by itself.

```python
config = TrainConfig(
    model=Model(),
    dataflow=train_df,              # or data=QueueInput(train_df)
    callbacks=[ModelSaver(), ...],  # user callbacks
    extra_callbacks=None,           # defaults are appended if None
    monitors=None,                  # default TensorBoard/JSON/stdout monitors
    session_init=SmartInit(load_path),
    steps_per_epoch=steps,
    starting_epoch=1,
    max_epoch=90)
launch_train_with_config(config, trainer)
```

Important behavior:

- `dataflow` and `data` are mutually exclusive.
- If `steps_per_epoch` is absent, Tensorpack tries to infer it from input size;
  with generators, streaming data, or custom input sources, set it explicitly.
- With `SimpleTrainer`, a bare DataFlow is fed directly. With non-simple
  trainers, launch applies queue/staging prefetching heuristics when possible.
- `extra_callbacks=None` means defaults are included. Use an explicit list to
  replace or customize defaults.
- `monitors=None` means default monitor backends are used.
- `AutoResumeTrainConfig` reads logger-dir checkpoint and JSON history; it does
  not infer custom checkpoint directories.

## Raw trainer control

Use raw control when `TrainConfig` is too early or too rigid.

```python
trainer = SimpleTrainer()
input_source = QueueInput(train_df)  # or another InputSource
model = Model()
trainer.setup_graph(
    model.get_input_signature(),
    input_source,
    model.build_graph,
    model.get_optimizer)

# Now callbacks can inspect graph/towers before training starts.
callbacks = [ModelSaver(), InferenceRunner(valid_df, [ScalarStats('total_cost')])]
trainer.train_with_defaults(
    callbacks=callbacks,
    extra_callbacks=None,
    monitors=None,
    session_init=SmartInit(load_path),
    steps_per_epoch=steps,
    starting_epoch=1,
    max_epoch=epochs)
```

Use raw control for:

- callbacks that need graph tensors created by `setup_graph()`;
- custom input-source or session-creator behavior;
- non-`TrainConfig` resumption policies;
- custom trainers whose `run_step()` is not simply optimizer minimization.

## Trainer selection

| Scenario | Recommended trainer | Reason | Required caution |
| --- | --- | --- | --- |
| CPU smoke, local development, one GPU | `SimpleTrainer()` | Single tower, minimal behavior. | Do not use it to claim multi-GPU behavior. |
| Local synchronized multi-GPU, simplest choice | `SyncMultiGPUTrainer(list_or_count)` | Uses Tensorpack default multi-GPU strategy. | Revisit batch size and `steps_per_epoch`. |
| Local synchronized multi-GPU, replicated variables | `SyncMultiGPUTrainerReplicated(gpus, average=True, mode=None)` | Efficient allreduce/aggregation choices. | BatchNorm/model variables can have sync caveats; mode heuristics depend on TF/GPU setup. |
| Local synchronized multi-GPU, shared variables | `SyncMultiGPUTrainerParameterServer(gpus, ps_device=None)` | Shared variable scope and averaged gradients. | `ps_device` CPU/GPU choice affects speed and memory. |
| Asynchronous local multi-GPU | `AsyncMultiGPUTrainer(gpus, scale_gradient=True)` | Towers independently apply updates. | Optimization semantics differ; use only deliberately. |
| Multi-machine or launcher-managed allreduce | `HorovodTrainer(average=True, compression=None)` | Horovod supports local and distributed allreduce. | Must launch with `horovodrun`; avoid CUDA context probes before trainer initialization. |
| Legacy TF parameter-server distributed | distributed parameter-server/replicated trainers | Exists for TF server clusters. | Deprecated/slow; prefer Horovod when possible. |
| BytePS deployment | `BytePSTrainer(average=True)` | BytePS-specific allreduce/push-pull behavior. | Requires BytePS environment/launcher; not CPU-smoke verified. |

### Multi-GPU batch and epoch rule

If a DataFlow yields batches of 32 and the trainer uses 4 towers, Tensorpack
consumes 4 batches per training step. The effective batch is 128. Adjust:

- learning rate schedules;
- number of steps per epoch;
- validation/checkpoint periods;
- any throughput callback that assumes samples per step.

## Tower-function rules

A `ModelDesc.build_graph()` method becomes the tower function. It must be safe
to call multiple times under different names and modes.

Do:

```python
with tf.variable_scope('block'):
    w = tf.get_variable('W', shape=[3, 3, 16, 32])
```

Do not:

```python
# Raw tf.Variable does not honor variable-scope reuse for trainable vars.
w = tf.Variable(tf.random_normal([3, 3, 16, 32]), name='W')
```

Checklist:

1. Use stable layer names such as `Conv2D('conv1', x, ...)`.
2. Do not build trainable variable names from tensor names or name scopes.
3. Do not mutate global Python state from `build_graph()` unless guarded; it may
   run once per GPU and again for inference.
4. Only trainable-by-gradient variables belong in `TRAINABLE_VARIABLES`.
5. Non-trainable state needed for inference should be in `MODEL_VARIABLES`.
6. Do not create variables or scopes containing the reserved word `tower`.
7. Use `self.training` to branch between training-only and inference-only paths.
8. For BatchNorm, rely on Tensorpack `BatchNorm` with `TowerContext` or pass
   `training=` explicitly. Keep `RunUpdateOps()` if update ops are created.

## Callbacks, monitors, and summaries

Training iteration order is conceptually:

```python
callbacks.setup_graph()
callbacks.before_train()
for epoch in range(starting_epoch, max_epoch + 1):
    callbacks.before_epoch()
    for local_step in range(steps_per_epoch):
        trainer.run_step()       # _before_run/_after_run hooks wrap this
        callbacks.trigger_step()
    callbacks.after_epoch()
    callbacks.trigger_epoch()
callbacks.after_train()
```

Common callback bundles:

```python
callbacks = [
    ModelSaver(max_to_keep=10),
    InferenceRunner(valid_df, [
        ScalarStats('total_cost'),
        ClassificationError('wrong', 'val-error')]),
    ScheduledHyperParamSetter('learning_rate',
                              [(1, 1e-3), (30, 1e-4), (60, 1e-5)]),
    MinSaver('val-error'),
]
```

Ordering matters:

- `ModelSaver` should appear before `MinSaver`/`MaxSaver` because best-saver
  callbacks copy the latest checkpoint.
- `InferenceRunner` must run before `MinSaver('val-error')` if it produces the
  monitored scalar.
- Custom callbacks are executed in list order at each callback phase.
- If validation depends on input tensors, prefer `InferenceRunner` or
  `_before_run`/`_after_run` hooks over ad-hoc extra `sess.run` calls that waste
  datapoints or bypass input-source hooks.

Summary flow:

1. In model code, add TensorFlow summaries or Tensorpack moving summaries.
2. `MovingAverageSummary` maintains moving-average values each step.
3. `MergeAllSummaries` evaluates summary ops every epoch by default or every
   `period` steps when configured.
4. Monitors dispatch scalars/summaries to TensorBoard events, JSON, and stdout.

Use a custom collection when frequent summaries are cheap and expensive image or
histogram summaries should stay infrequent.

## Session initialization and resume

Training script patterns:

```python
config = TrainConfig(..., session_init=SmartInit(load_path))
```

or:

```python
config = AutoResumeTrainConfig(
    always_resume=True,
    model=Model(), dataflow=train_df,
    callbacks=[ModelSaver()], steps_per_epoch=steps, max_epoch=epochs)
```

Rules:

- `SmartInit(None)` or `SmartInit('')` is a no-op.
- Use checkpoint/npz inspection and export guidance from
  `../inference-export/SKILL.md`; this file only wires initialization into
  training.
- `AutoResumeTrainConfig` expects logger-dir checkpoint plus JSON history. If
  checkpoints are saved elsewhere, use explicit `session_init` and
  `starting_epoch`.

## Symbolic layers workflow

Use Tensorpack layers when you want their legacy variable names, default
initializers, `argscope`, `LinearWrap`, and `TowerContext` integration. You can
also use TensorFlow symbolic functions directly.

```python
with argscope([Conv2D, BatchNorm], data_format='channels_first'), \
     argscope(Conv2D, kernel_size=3, activation=tf.nn.relu, use_bias=False):
    net = Conv2D('conv0', image, 32)
    net = BatchNorm('bn0', net)
    net = FullyConnected('fc', net, 10, activation=tf.identity)
```

Use `LinearWrap` only for linear pipelines:

```python
logits = (LinearWrap(image)
          .Conv2D('conv0', 32, 3, activation=tf.nn.relu)
          .MaxPooling('pool0', 2)
          .FullyConnected('logits', 10, activation=tf.identity)())
```

Avoid `LinearWrap` for branches, skip connections, multi-input layers, or when
you need direct access to intermediate tensors.

### Tensorpack versus `tf.layers`/Keras

- Tensorpack layers often call TF layer implementations but preserve Tensorpack
  defaults and variable names.
- Tensorpack does not require Tensorpack layers; any symbolic TensorFlow graph
  can be used inside `build_graph()` if it respects tower rules.
- `tf.layers`/slim/tensorlayer usually respect variable scopes; still verify
  variable collections and update ops.
- Keras/Sonnet-style model classes can manage variable scopes internally and may
  create new scopes on repeated calls. Treat Tensorpack+Keras as experimental
  and read [troubleshooting.md](troubleshooting.md#keras-and-other-symbolic-libraries)
  before recommending it.

## Custom callback pattern

Subclass `Callback` and implement underscore-prefixed hooks.

```python
from tensorpack.callbacks import Callback

class PutLearningRate(Callback):
    def _setup_graph(self):
        self.lr = self.graph.get_tensor_by_name('learning_rate:0')

    def _trigger_epoch(self):
        value = self.trainer.sess.run(self.lr)
        self.trainer.monitors.put_scalar('debug/lr', value)
```

Use `_setup_graph` for tensors/ops, `_before_run`/`_after_run` for work that
must happen in the same session run as the training op, `_trigger_step` for
light step-level work, and `_trigger_epoch`/`_trigger` for epoch-level work.
Raise `StopTraining` for a controlled stop.

## Custom trainer pattern

Try a callback first. Write a custom trainer only when the iteration itself is
not the usual one-cost-one-optimizer update.

Options:

1. Create graph tensors/ops before constructing the trainer, or in
   `Trainer.__init__`.
2. Set `self.train_op` and rely on the default `run_step()`.
3. Override `run_step()` when one iteration must run several operations or use
   custom Python logic.

When using more than one `Session.run`, choose `self.sess` versus
`self.hooked_sess` deliberately. `hooked_sess` triggers callback hooks and
input-source machinery; plain `sess` does not.

## Custom layer pattern

A Tensorpack layer is a symbolic function registered with layer metadata:

```python
from tensorpack.models import layer_register

@layer_register(log_shape=True)
def MyLayer(x, units, activation=tf.identity):
    w = tf.get_variable('W', [x.shape[-1], units])
    y = tf.matmul(x, w)
    return activation(y, name='output')
```

Rules:

- First argument is the input tensor or list of tensors.
- Return a tensor or list of tensors.
- Registered layers are called with a scope name: `MyLayer('name', x, units)`.
- `argscope` works for arguments other than the input tensor(s).
- `LinearWrap` works when the layer has one input and one output.

## Verification workflow for generated scripts

Use the bundled helper for a fast Tensorpack framework smoke check:

```bash
python ../scripts/minimal_training_smoke.py --help
python ../scripts/minimal_training_smoke.py --workdir /tmp/tensorpack-smoke --steps-per-epoch 2 --max-epoch 1
```

The smoke helper verifies fake-data graph building, summaries, callbacks, model
saving, validation inference, and `SimpleTrainer` launch. It does **not** verify
real data loading, GPU scaling, Horovod, BytePS, or claimed benchmark metrics.
