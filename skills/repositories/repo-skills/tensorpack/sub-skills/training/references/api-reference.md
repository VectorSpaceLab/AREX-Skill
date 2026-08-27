# Tensorpack training API reference

This reference distills verified Tensorpack 0.11 API facts for training tasks.
Prefer these signatures over memory. For long workflows and examples, return to
[../SKILL.md](../SKILL.md) and [workflows.md](workflows.md).

## Model definitions

### `ModelDescBase` and `ModelDesc`

- `ModelDesc()` is the single-cost, single-optimizer model interface used by
  the high-level training path.
- Implement these methods in a subclass:
  - `inputs(self) -> list[tf.TensorSpec | tf.placeholder]`: declares input
    shape, dtype, and name. If placeholders are returned, create them inside
    `inputs()`; do not return placeholders made elsewhere.
  - `build_graph(self, *args)`: builds the tower function. In a `ModelDesc`, it
    must return the final cost tensor when called under training mode. Include
    regularization in this cost.
  - `optimizer(self) -> tf.train.Optimizer`: returns a TF1 optimizer. Tensorpack
    memoizes the value through `get_optimizer()` and asserts it is a
    `tf.train.Optimizer` instance.
- Helper properties/methods:
  - `get_input_signature()` caches a list of `tf.TensorSpec` derived from
    `inputs()`.
  - `input_names` returns names from the input signature.
  - `training` returns the current tower context's training/inference boolean.

Minimal shape:

```python
class Model(ModelDesc):
    def inputs(self):
        return [tf.TensorSpec((None, 28, 28, 1), tf.float32, 'image'),
                tf.TensorSpec((None,), tf.int32, 'label')]

    def build_graph(self, image, label):
        logits = FullyConnected('logits', image, 10, activation=tf.identity)
        loss = tf.nn.sparse_softmax_cross_entropy_with_logits(
            logits=logits, labels=label)
        return tf.reduce_mean(loss, name='total_cost')

    def optimizer(self):
        return tf.train.AdamOptimizer(1e-3)
```

## Training configuration and launch

| API | Verified signature | Role |
| --- | --- | --- |
| `TrainConfig` | `TrainConfig(dataflow=None, data=None, model=None, callbacks=None, extra_callbacks=None, monitors=None, session_creator=None, session_config=None, session_init=None, starting_epoch=1, steps_per_epoch=None, max_epoch=99999)` | High-level bundle for a single-cost trainer. Accept either `dataflow` or `data`, not both. |
| `AutoResumeTrainConfig` | `AutoResumeTrainConfig(always_resume=True, **kwargs)` | Same arguments as `TrainConfig`, plus heuristics that load latest checkpoint and JSON epoch history from the logger directory. |
| `launch_train_with_config` | `launch_train_with_config(config, trainer)` | Applies default input prefetching, calls `trainer.setup_graph(...)`, checks unused regularization, then calls `trainer.train_with_defaults(...)`. |

`TrainConfig` details agents often need:

- `dataflow` must be a Tensorpack `DataFlow`. If supplied with
  `SimpleTrainer`, launch uses a feed input; for other trainers, launch may wrap
  the dataflow in queue/staging inputs. For complex input-source design, route
  to the dataflow sub-skill.
- `data` must be an `InputSource` such as a queue or feed input.
- `callbacks` are user callbacks. `extra_callbacks` defaults to the default
  callback list and is concatenated after `callbacks`.
- `monitors` defaults to TensorBoard events, JSON history, and scalar printing.
- `session_init` accepts a Tensorpack session initializer such as
  `SmartInit(...)` or `SaverRestore(...)`.
- If `steps_per_epoch` is omitted, Tensorpack tries `len(dataflow)` or
  `data.size()`. If size is unavailable, set `steps_per_epoch` explicitly.
- `steps_per_epoch` schedules callbacks. It does not by itself change which
  datapoints are consumed.

`launch_train_with_config` is mostly equivalent to:

```python
trainer.setup_graph(
    model.get_input_signature(), input_source,
    model.build_graph, model.get_optimizer)
trainer.train_with_defaults(
    callbacks=config.callbacks,
    monitors=config.monitors,
    session_creator=config.session_creator,
    session_init=config.session_init,
    steps_per_epoch=config.steps_per_epoch,
    starting_epoch=config.starting_epoch,
    max_epoch=config.max_epoch,
    extra_callbacks=config.extra_callbacks)
```

Use raw trainer control when you need to build callbacks after graph setup or
when the training loop is not single-cost optimization.

## Trainers and launch

| API | Verified signature | Use when | Caveats |
| --- | --- | --- | --- |
| `SimpleTrainer` | `SimpleTrainer(*args, **kwargs)` | CPU, one local GPU, or the simplest single-tower training loop. | Builds one training tower. |
| `SyncMultiGPUTrainer` | `SyncMultiGPUTrainer(gpus)` | You want Tensorpack's default synchronized multi-GPU trainer. | Convenience wrapper; may not be fastest. |
| `SyncMultiGPUTrainerParameterServer` | `SyncMultiGPUTrainerParameterServer(gpus, ps_device=None)` | Synchronized data-parallel training with shared variables placed on CPU or GPU parameter-server style. | For more than one GPU, input must be feed-free; launcher may queue/stage a DataFlow. |
| `SyncMultiGPUTrainerReplicated` | `SyncMultiGPUTrainerReplicated(gpus, average=True, mode=None)` | Synchronized replicated training with gradient aggregation (`nccl`, `hierarchical`, `cpu`, or `gpu` heuristics). | BatchNorm/model variables may not be perfectly synchronized; `BROADCAST_EVERY_EPOCH` exists to help. |
| `AsyncMultiGPUTrainer` | `AsyncMultiGPUTrainer(gpus, scale_gradient=True)` | Intentionally asynchronous local multi-GPU updates. | Towers update shared variables independently; convergence semantics differ from synchronous SGD. |
| `DistributedTrainerParameterServer` | source-backed `DistributedTrainerParameterServer(gpus, server, caching_device='cpu')` | Legacy distributed parameter-server training. | Deprecated/slow; requires `tf.train.Server` cluster setup. |
| `DistributedTrainerReplicated` | source-backed `DistributedTrainerReplicated(gpus, server)` | Legacy distributed replicated training. | Deprecated/slow; requires `tf.train.Server` and careful variable synchronization. |
| `HorovodTrainer` | `HorovodTrainer(average=True, compression=None)` | Horovod multi-GPU or multi-machine allreduce. | Requires Horovod launcher/dependency. Avoid CUDA context initialization before trainer starts. |
| `BytePSTrainer` | source-backed `BytePSTrainer(average=True)` | BytePS-style distributed training. | Requires BytePS launcher environment variables and best-practice setup. |

Multi-GPU semantics: Tensorpack does **not** split a single input batch across
GPUs. Each tower obtains a batch from the input, so total batch size is
`per_input_batch * number_of_towers`. Revisit learning rate and
`steps_per_epoch` whenever the number of GPUs changes.

## Tower context and tower-function APIs

| API | Role |
| --- | --- |
| `TowerContext(name, is_training)` / training and prediction tower contexts | Context in which tower functions are called; controls training/inference mode and tower name. |
| `get_current_tower_context()` | Read current context from inside model code or callbacks. |
| `trainer.tower_func.towers` / tower handles | Access tensors built in training/inference towers from callbacks. |
| `trainer.get_predictor()` | Create a callable predictor under inference mode inside a callback. |

Tower function rules:

1. It may be called multiple times for multiple GPUs and inference callbacks.
2. Put only gradient-trainable variables in `TRAINABLE_VARIABLES`.
3. Put non-trainable variables needed for inference in `MODEL_VARIABLES`.
4. Use `tf.get_variable`, not raw `tf.Variable`, for trainable variables that
   must respect variable-scope reuse.
5. Do not make variable names depend on tensor names or name scopes.
6. Do not create scopes or variables containing `tower`; Tensorpack reserves it.
7. Use `self.training` or `get_current_tower_context().is_training` for
   train/inference branches.

## Callbacks, inferencers, and monitors

| API | Verified signature | Role and notes |
| --- | --- | --- |
| `ModelSaver` | `ModelSaver(max_to_keep=10, keep_checkpoint_every_n_hours=0.5, checkpoint_dir=None, var_collections=None)` | Saves checkpoints when triggered. Defaults to logger directory and global variables. |
| `MinSaver` | source-backed `MinSaver(monitor_stat, reverse=False, filename=None, checkpoint_dir=None)` | Copies the latest checkpoint when a monitored scalar reaches a new minimum. Place after the callback that writes the scalar and after `ModelSaver`. |
| `MaxSaver` | source-backed `MaxSaver(monitor_stat, filename=None, checkpoint_dir=None)` | Same as `MinSaver` but keeps the maximum. |
| `InferenceRunner` | `InferenceRunner(input, infs, tower_name='InferenceTower', tower_func=None, device=0)` | Runs inferencers on an input source/dataflow, typically once per epoch. Builds an inference tower unless a tower function is supplied. |
| `ScalarStats` | `ScalarStats(names, prefix='validation')` | Averages scalar tensor values over validation datapoints. Batch average is not necessarily exact dataset accuracy. |
| `ClassificationError` | `ClassificationError(wrong_tensor_name='incorrect_vector', summary_name='validation_error')` | Computes true classification error from a boolean/binary wrong-vector tensor, e.g. `1 - tf.nn.in_top_k(...)`. |
| `ScheduledHyperParamSetter` | `ScheduledHyperParamSetter(param, schedule, interp=None, step_based=False, set_at_beginning=True)` | Sets a named hyperparameter or `HyperParam` object from an epoch- or step-based schedule. |
| `MovingAverageSummary` | `MovingAverageSummary(collection='MOVING_SUMMARY_OPS', train_op=None)` | Maintains moving-average summary variables every step. Default callback. |
| `MergeAllSummaries` | `MergeAllSummaries(period=0, run_alone=False, key=None)` | Merges summaries and writes them to monitors every epoch or every `period` steps. Default callback. |
| `RunUpdateOps` | `RunUpdateOps(collection=None)` | Runs update ops, defaulting to `UPDATE_OPS`, along with each training step. Default callback; important for BatchNorm. |
| `ProgressBar` | `ProgressBar(names=())` | Displays tqdm progress. Default callback. |
| `TFEventWriter` | `TFEventWriter(logdir=None, max_queue=10, flush_secs=120, **kwargs)` | Writes TensorBoard event files. Default monitor. |
| `JSONWriter` | `JSONWriter()` | Writes scalar history JSON under the logger directory and can append to previous history. Default monitor. |
| `ScalarPrinter` | `ScalarPrinter(enable_step=False, enable_epoch=True, whitelist=None, blacklist=None)` | Prints scalar monitor data. Default monitor. |

Default callbacks from `DEFAULT_CALLBACKS()` are:

1. `MovingAverageSummary()`
2. `ProgressBar()`
3. `MergeAllSummaries()`
4. `RunUpdateOps()`

Default monitors from `DEFAULT_MONITORS()` are:

1. `TFEventWriter()`
2. `JSONWriter()`
3. `ScalarPrinter()`

## Symbolic layers and summaries

Tensorpack layer functions are decorated layers. The verified installed
signature exposes the inner symbolic signature, while common Tensorpack code
passes a variable-scope name first, for example `Conv2D('conv0', image, 32, 3)`.

| API | Verified inner signature | Role and caveats |
| --- | --- | --- |
| `Conv2D` | `Conv2D(inputs, filters, kernel_size, strides=(1, 1), padding='same', data_format='channels_last', dilation_rate=(1, 1), activation=None, use_bias=True, kernel_initializer=None, bias_initializer=Zeros, kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, split=1)` | Similar to `tf.layers.Conv2D`, default variance-scaling kernel initializer, default `padding='same'`, supports grouped convolution by `split`. Variables are named under the layer scope. |
| `FullyConnected` | `FullyConnected(inputs, units, activation=None, use_bias=True, kernel_initializer=None, bias_initializer=Zeros, kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None)` | Dense wrapper with default variance-scaling kernel initializer and variables `W`/`b`. Flattens all non-batch dimensions first. |
| `BatchNorm` | `BatchNorm(inputs, axis=None, *, training=None, momentum=0.9, epsilon=1e-05, center=True, scale=True, beta_initializer=Zeros, gamma_initializer=Ones, virtual_batch_size=None, data_format='channels_last', ema_update='default', sync_statistics=None)` | More capable TF layer wrapper. If `training` is omitted, it uses `TowerContext` training/inference mode. Update semantics depend on `RunUpdateOps`. |
| `argscope` | `argscope(layers, **kwargs)` | Context manager that supplies default keyword arguments to a layer or list of layers. Explicit arguments override argscope defaults. |
| `LinearWrap` | `LinearWrap(tensor)` | Syntax sugar for linear chains of one-input/one-output symbolic functions. Avoid it when graph branches or tensor reuse become non-linear. |
| `regularize_cost` | source-backed `regularize_cost(regex, func, name='regularize_cost')` | Adds regularization cost over variables matched by regex; manually add the result to the model's final cost. |

Summary helpers:

| API | Verified signature | Role |
| --- | --- | --- |
| `summary.add_moving_summary` | `add_moving_summary(*args, **kwargs)` | Adds scalar tensors to the moving-summary collection. No-op outside the main training tower. |
| `summary.add_param_summary` | `add_param_summary(*summary_lists, **kwargs)` | Adds parameter summaries for trainable variables matching regexes, such as histograms or RMS. No-op outside the main training tower. |
| `tf.summary.*` | TensorFlow API | Adds summaries to graph collections. `MergeAllSummaries` decides when to evaluate them; monitors decide where to write them. |

## Optimizer helpers

`ModelDesc.optimizer()` may return a raw TF1 optimizer or a Tensorpack-wrapped
optimizer. Useful source-backed helpers include:

| API | Signature | Role |
| --- | --- | --- |
| `apply_grad_processors` | `apply_grad_processors(opt, gradprocs)` | Wrap an optimizer so gradient processors run before variable updates. |
| `AccumGradOptimizer` | `AccumGradOptimizer(opt, niter)` | Accumulates gradients across `niter` executions and applies them together. |
| `GlobalNormClip` | source-backed `GlobalNormClip(clip_norm)` | Gradient processor for global norm clipping. |
| `SummaryGradient` | source-backed `SummaryGradient(regex='.*')` | Adds summaries for selected gradients. |

Example pattern:

```python
from tensorpack.tfutils import optimizer
from tensorpack.tfutils.gradproc import GlobalNormClip, SummaryGradient

base = tf.train.AdamOptimizer(learning_rate)
return optimizer.apply_grad_processors(base, [GlobalNormClip(5), SummaryGradient()])
```

## Session init and resume touchpoints

Training only owns how session initialization is wired. For checkpoint variable
inspection, export, or offline prediction, use the inference-export sub-skill.

| API | Verified signature | Role |
| --- | --- | --- |
| `SmartInit` | `SmartInit(obj, *, ignore_mismatch=False)` | Creates a session initializer from a checkpoint path, dict, `.npz`, empty string, or `None`. |
| `SaverRestore` | `SaverRestore(model_path, prefix=None, ignore=())` | Restores a checkpoint saved by a TF saver or `ModelSaver`. |
| `TrainConfig(session_init=...)` | see `TrainConfig` | Preferred high-level place to load initial weights. |
| `AutoResumeTrainConfig` | see above | Restarts from logger-dir checkpoint plus JSON epoch history when available. |

Do not confuse checkpoint **loading for training** with checkpoint **inspection or
export**. Use this sub-skill for the former and route the latter to
`../inference-export/SKILL.md`.
