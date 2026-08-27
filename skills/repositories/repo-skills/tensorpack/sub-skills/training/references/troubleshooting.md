# Tensorpack training troubleshooting

Use this when a Tensorpack training script fails, produces missing metrics, or
behaves differently after changing trainer/backend. For API signatures, see
[api-reference.md](api-reference.md); for patterns, see [workflows.md](workflows.md).

## TF1 graph mode and eager execution

### Symptom

- `RuntimeError` or TensorFlow errors mention eager execution, placeholders,
  sessions, graph finalization, `tf.TensorSpec`, or `tf.placeholder`.
- A script works under old TF1 examples but fails with a TF2 package.

### Likely cause

Tensorpack training is TF1-graph-oriented. The high-level launch path disables
eager execution when it detects TF2, but code that creates tensors/placeholders
before launch may already be in the wrong mode.

### Recovery

1. Import and use `tensorpack.tfv1` or `tf.compat.v1` style APIs.
2. Call `tf.disable_eager_execution()` /
   `tf.compat.v1.disable_eager_execution()` before graph construction.
3. Avoid TF2/Keras eager-only objects inside `ModelDesc.build_graph()`.
4. Reset the default graph between repeated smoke runs in one Python process.
5. If using external symbolic libraries, verify they build graph tensors and
   honor variable scopes.

## `steps_per_epoch` and epoch semantics

### Symptom

- `You must set TrainConfig(steps_per_epoch)` appears.
- Validation/checkpointing happens too often or too rarely.
- After changing GPU count, total epochs no longer match the intended number of
  dataset passes.

### Likely cause

Tensorpack epochs schedule callbacks; they are not intrinsically full passes
over data. If input size is unavailable, `TrainConfig` cannot infer
`steps_per_epoch`. In multi-GPU training, each tower consumes a full input batch.

### Recovery

1. Set `TrainConfig(steps_per_epoch=<int>)` explicitly for generators,
   streaming data, or custom `InputSource` objects.
2. Define what one epoch means for the task: examples, environment transitions,
   optimizer updates, or validation/checkpoint period.
3. For multi-GPU, compute effective batch as
   `input_batch_per_tower * number_of_towers`.
4. Re-scale learning rate, LR schedule milestones, checkpoint period, and
   validation period after changing tower count.
5. For performance/data pipeline issues, route to `../dataflow/SKILL.md`.

## Tensor shapes, input names, and tensor names

### Symptom

- `inputs() should return a list of tf.TensorSpec objects`.
- `build_graph()` receives tensors in the wrong order.
- `InferenceRunner` or `ScalarStats` cannot find a tensor by name.
- A classification error callback reports missing `wrong`/`incorrect_vector`.

### Likely cause

`inputs()` metadata does not match the dataflow/input-source datapoints, tensor
names are not stable, or callback names target tensors that were never named.

### Recovery

1. Ensure `inputs()` returns a list/tuple matching the datapoint order exactly.
2. Use stable names in `tf.TensorSpec(..., name='input')` and named reductions:
   `tf.reduce_mean(loss, name='total_cost')`.
3. For labels shaped `[B, 1]`, reshape or squeeze to `[B]` before sparse loss.
4. For `ScalarStats('total_cost')`, create a tensor named `total_cost` in the
   graph. For tower tensors, Tensorpack can resolve from the tower handles.
5. For `ClassificationError`, create a wrong-vector tensor:

```python
wrong = tf.logical_not(tf.nn.in_top_k(predictions=logits, targets=label, k=1))
wrong = tf.cast(wrong, tf.float32, name='wrong')
callbacks = [InferenceRunner(valid_df, [ClassificationError('wrong', 'val-error')])]
```

6. Print `tensor.name` in a small graph smoke before wiring callbacks.
7. Do not build variable or scope names from tensor names; this breaks tower
   reuse.

## Tower variable scope and reuse failures

### Symptom

- Errors mention variables already existing, variables not existing with
  `reuse=True`, or duplicated scopes in multi-GPU/inference.
- A model works with `SimpleTrainer` but fails with multi-GPU or validation
  `InferenceRunner`.

### Likely cause

The tower function is called more than once. Trainable variables must be created
with `tf.get_variable` through stable variable scopes. Some external layers or
Keras/Sonnet-style modules do not respect TensorFlow variable-scope reuse.

### Recovery

1. Use Tensorpack layer calls with stable names, e.g. `Conv2D('conv0', x, ...)`.
2. For custom trainable variables, use `tf.get_variable` inside explicit scopes.
3. Do not call `scope.reuse_variables()` on scopes you did not create.
4. Do not create scopes or variables containing the reserved word `tower`.
5. Avoid global-state mutation in `build_graph()`; if unavoidable, guard by
   `self.training` or by tower context.
6. If a failure only appears when validation is added, remember
   `InferenceRunner` builds an inference tower. Test a graph under both training
   and inference tower contexts.
7. For Keras, see [Keras and other symbolic libraries](#keras-and-other-symbolic-libraries).

## Callbacks, monitors, and validation

### Symptom

- No TensorBoard events, no JSON history, or no scalar printouts appear.
- `MinSaver`/`MaxSaver` does nothing or saves the wrong checkpoint.
- Validation metrics are missing or stale.
- Custom callback creates ops during training and hits graph-finalization errors.

### Likely cause

Default callbacks/monitors were replaced, callback ordering is wrong, the
monitored statistic name is wrong, or the callback created graph ops after the
graph was finalized.

### Recovery

1. If you set `extra_callbacks=[]`, you removed defaults. Re-add needed defaults
   or set `extra_callbacks=None`.
2. Defaults normally include:
   - callbacks: moving summaries, progress bar, merged summaries, update ops;
   - monitors: TensorBoard event writer, JSON writer, scalar printer.
3. Place `ModelSaver` before `MinSaver`/`MaxSaver`.
4. Place the metric-producing callback, often `InferenceRunner`, before the
   best-checkpoint saver targeting that metric.
5. Match metric names exactly: `MinSaver('val-error')` requires a monitor scalar
   named `val-error`.
6. Create tensors/ops in callback `_setup_graph()`, not in `_trigger_epoch()` or
   training loops.
7. If callback logic depends on inputs, implement `_before_run`/`_after_run` so
   it runs with the training step instead of consuming extra datapoints.
8. Ensure `logger.set_logger_dir(...)` is called before callbacks that write
   files, or pass explicit checkpoint/log directories.

## Checkpoint load, resume, and logger directory

### Symptom

- Training starts from scratch unexpectedly.
- `AutoResumeTrainConfig` does not resume.
- A checkpoint is saved but `MinSaver` cannot find a checkpoint state.
- Loading a `.npz` or checkpoint gives variable-name/shape errors.

### Likely cause

Resume state is split between logger directory checkpoint state and JSON history;
manual checkpoint directories do not match; or variable names/shapes changed.

### Recovery

1. For simple loading, set `TrainConfig(session_init=SmartInit(load_path))`.
2. For logger-dir auto-resume, use `AutoResumeTrainConfig` and keep both
   checkpoint state and JSON history in the logger directory.
3. If `ModelSaver(checkpoint_dir=...)` uses a non-default directory, make
   `MinSaver/MaxSaver(checkpoint_dir=...)` match it.
4. Put `ModelSaver` earlier in callbacks than `MinSaver`/`MaxSaver`.
5. For variable listings, shape mismatches, `.npz` contents, or export, route to
   `../inference-export/SKILL.md`.
6. Do not set `ignore_mismatch=True` blindly; it can mask real model changes.

## BatchNorm and update ops

### Symptom

- Training loss changes, but validation is poor or unstable.
- BatchNorm moving averages are not updated.
- Multi-GPU validation differs from single-GPU in suspicious ways.

### Likely cause

BatchNorm behavior depends on training/inference mode and update ops. Tensorpack
`BatchNorm` uses `TowerContext` when `training` is omitted. Moving-average
updates are often in `UPDATE_OPS` and are run by the default `RunUpdateOps()`
callback.

### Recovery

1. Keep default callbacks or explicitly include `RunUpdateOps()`.
2. If using non-Tensorpack BN layers, confirm their update ops land in
   `tf.GraphKeys.UPDATE_OPS` and should be run every step.
3. Use `self.training` or `TowerContext.is_training` consistently for dropout,
   BN, and inference-only branches.
4. In replicated/Horovod training, remember non-master workers may not maintain
   identical moving averages. Review trainer-specific broadcast/sync behavior
   before comparing metrics.
5. When freezing variables with `tf.stop_gradient` or gradient processors,
   remember BN statistics can still update via update ops.

## GPU and multi-GPU semantics

### Symptom

- Effective batch size is larger than expected.
- Accuracy changes after moving from one GPU to many GPUs.
- Multi-GPU trainer asserts that input must be feed-free.
- Horovod job hangs or conflicts with multiprocessing/dataflow.

### Likely cause

Tensorpack multi-GPU trainers let each GPU pull an input batch. They do not
split one batch tensor. Multi-GPU trainers also require queue/staging/feed-free
input paths, and Horovod has launcher and CUDA-context constraints.

### Recovery

1. Compute effective batch size as `batch_per_input * number_of_towers`.
2. Adjust `steps_per_epoch` and LR schedule milestones for the new effective
   batch and number of updates.
3. Use `SyncMultiGPUTrainerReplicated` or `SyncMultiGPUTrainerParameterServer`
   intentionally; do not switch trainer just for speed without revisiting
   optimizer semantics.
4. If using `SyncMultiGPUTrainerReplicated`, choose aggregation mode only when
   you understand hardware and TensorFlow version constraints. Otherwise use
   `mode=None` heuristics.
5. For Horovod:
   - launch with `horovodrun`/MPI/Gloo as appropriate;
   - avoid `tf.test.is_gpu_available()` or device-listing calls that initialize
     CUDA before trainer setup;
   - ensure one process per GPU has a non-conflicting log directory;
   - watch for multiprocessing dataflow conflicts with MPI/fork.
6. Treat GPU/distributed advice as unverified until the user supplies matching
   hardware and dependencies.

## CPU-only environment issues

### Symptom

- `tf.test.is_gpu_available()` assertions fail.
- CPU run fails with NCHW/channel-first convolution errors.
- ImageNet/ResNet/FasterRCNN examples build but cannot train usefully.

### Likely cause

Some example code assumes GPU or uses ops/layouts unsupported by CPU TensorFlow.
The generated Tensorpack skill's required verification backend is CPU; large
GPU recipes are documented but not verified.

### Recovery

1. For framework sanity, run the fake-data smoke helper.
2. For CPU debug, prefer `channels_last`/NHWC model code unless the example
   requires GPU-specific layout.
3. Remove hard GPU assertions for CPU-only smoke only when you are not claiming
   original benchmark behavior.
4. Ask for GPU hardware and the matching TensorFlow backend before promising
   multi-GPU or performance reproduction.

## Keras and other symbolic libraries

### Symptom

- Keras model creates duplicate variables across towers.
- Keras training/inference mode is wrong during validation.
- Tensorpack multi-GPU/inference works with native layers but not Keras layers.

### Likely cause

Tensorpack expects tower functions to respect TensorFlow variable scopes and
reuse. Keras model objects can manage scopes and learning phase internally.
Tensorpack's Keras wrapper exists but is experimental.

### Recovery

1. Prefer native Tensorpack layers or plain TensorFlow symbolic functions for new
   Tensorpack scripts.
2. If reusing Keras is required, wrap construction in the documented Keras
   helper pattern and test both training and inference towers.
3. Add the Keras phase callback/hook when the model uses Keras learning phase.
4. Avoid recommending Tensorpack+Keras for new code unless the user explicitly
   needs it and accepts compatibility risk.

## Callback-driven debugging

### Symptom

- Need to inspect intermediate tensors during training.
- Adding print/session calls changes input consumption or slows training.

### Recovery

1. For quick tensor debug, use TF graph printing:

```python
tensor = tf.Print(tensor, [tf.shape(tensor), tensor], tensor.name, summarize=100)
```

2. For scalar progress, add `summary.add_moving_summary(...)` or
   `tf.summary.scalar(...)` and rely on default monitors.
3. For custom debug logic, create a callback and place tensor lookup in
   `_setup_graph()`.
4. Use `_before_run`/`_after_run` for tensors that depend on input datapoints;
   this avoids wasting data by calling a separate `sess.run()`.
5. Use `ProgressBar(names=[...])` when step-level terminal printing is desired.

## Data/input failures during training

### Symptom

- Training stalls with low queue size.
- Multi-process input repeats samples or validation order changes.
- `QueueInput`, `StagingInput`, or DataFlow wrappers behave unexpectedly.

### Route

This sub-skill only covers how input connects to training. Detailed DataFlow
construction, serializer dependencies, multiprocessing, reset-state behavior,
randomness, and performance tuning are owned by `../dataflow/SKILL.md`.

Immediate checks:

1. Confirm dataflow datapoint shapes match `inputs()`.
2. Confirm batches are produced before multi-GPU trainers pull one batch per
   tower.
3. Keep validation deterministic and order-preserving unless metrics are order
   invariant.
4. Run DataFlow speed/profiling guidance from the dataflow sub-skill before
   changing model/trainer code.

## When to stop and ask for more information

Stop and ask before claiming success when any of these are missing:

- required dataset path/layout (ImageNet, COCO, TIMIT, Atari ROMs, PTB, etc.);
- GPU/Horovod/BytePS backend required by the intended trainer;
- exact checkpoint or `.npz` file for resume/evaluation;
- target metric and acceptable tolerance;
- dependency permission for optional packages such as pycocotools, Gym/ALE,
  Caffe bindings, or audio feature libraries.
