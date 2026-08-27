---
name: training
description: "Use Tensorpack ModelDesc, TrainConfig, trainers, callbacks,
  summaries, layers, and example training recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensorpack training sub-skill

Use this sub-skill when a task needs Tensorpack graph training: defining a
`ModelDesc`, choosing a trainer, configuring `TrainConfig`, composing callbacks
and monitors, using Tensorpack symbolic layers, adapting known training recipes,
or debugging TF1-compatible tower training.

## Start here

1. If the user needs a training script skeleton, read
   [references/workflows.md](references/workflows.md#minimal-modeldesc--trainconfig-quickstart)
   and consider the bundled smoke helper
   [scripts/minimal_training_smoke.py](scripts/minimal_training_smoke.py).
2. If the user asks for an API name, signature, or role, read
   [references/api-reference.md](references/api-reference.md).
3. If the user asks how to adapt an example family such as MNIST, ResNet,
   Faster/Mask R-CNN, GAN, Atari RL, TIMIT, Char-RNN, PTB, or Keras, read
   [references/example-recipes.md](references/example-recipes.md).
4. If the user reports an error, wrong metric, checkpoint/resume issue, GPU
   scaling surprise, Keras incompatibility, or TF2/eager-mode failure, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. For deeper patterns, use
   [references/workflows.md](references/workflows.md) before proposing code.

## Route to this sub-skill when

- The task mentions `ModelDesc`, `ModelDescBase`, `inputs()`, `build_graph()`,
  `optimizer()`, `TrainConfig`, `AutoResumeTrainConfig`, or
  `launch_train_with_config`.
- The task asks how Tensorpack follows the define-then-run paradigm, how an
  epoch/step loop works, or how callbacks fit around training iterations.
- The task asks which trainer to use: `SimpleTrainer`,
  `SyncMultiGPUTrainer`, `SyncMultiGPUTrainerReplicated`,
  `SyncMultiGPUTrainerParameterServer`, `AsyncMultiGPUTrainer`, distributed
  parameter-server/replicated trainers, `HorovodTrainer`, or BytePS-style
  distributed trainers.
- The task involves tower-function rules: variable scopes, variable reuse,
  collections, train/inference towers, `TowerContext`, or multiple calls to
  the same tower function.
- The task involves callbacks/monitors such as `ModelSaver`, `InferenceRunner`,
  `ScalarStats`, `ClassificationError`, `ScheduledHyperParamSetter`,
  `MaxSaver`, `MinSaver`, `MergeAllSummaries`, TensorBoard event files,
  JSON histories, scalar printing, progress bars, or update ops.
- The task involves training summaries: `tf.summary.*`,
  `summary.add_moving_summary`, `summary.add_param_summary`, moving averages,
  default monitors, or logging into TensorBoard/JSON/stdout.
- The task involves Tensorpack symbolic layers such as `Conv2D`,
  `FullyConnected`, `BatchNorm`, `argscope`, `LinearWrap`, `regularize_cost`,
  `BNReLU`, pooling layers, dropout, or caveats around `tf.layers`/Keras.
- The task asks how to adapt a Tensorpack example family for training, while
  preserving data, dependency, and backend caveats.

## Route elsewhere

- For DataFlow construction, dataset layout, serializers, augmentors, input
  performance, queue stalls, or `MultiProcessRunnerZMQ`, route to
  [../dataflow/SKILL.md](../dataflow/SKILL.md).
- For offline prediction, `PredictConfig`, `OfflinePredictor`, checkpoint
  variable inspection, `.npz` model-zoo files, Serving export, compact frozen
  graphs, or Caffe conversion, route to
  [../inference-export/SKILL.md](../inference-export/SKILL.md).
- For full benchmark/performance reproduction, ask for the actual hardware,
  exact dataset, cached weights, and dependency versions. Without those, only
  provide implementation guidance and verification limits.

## Operating checklist

1. **Normalize the objective.** Identify whether the user wants a new training
   script, a trainer choice, a callback/monitor setup, an example adaptation, or
   a debugging plan.
2. **Select the model interface.** Prefer `ModelDesc` + `TrainConfig` for
   single-cost gradient training. Use the raw trainer interface when callbacks
   must be constructed after graph setup or the iteration is not single-cost.
3. **Define inputs explicitly.** `inputs()` should return a list of
   `tf.TensorSpec` or placeholders created inside `inputs()`. The order and
   names must match the datapoints yielded by the input source.
4. **Build a tower-safe graph.** `build_graph()` is a tower function: it may be
   called once per GPU and again for inference. Use `tf.get_variable`, respect
   the enclosing variable scope, avoid global-state mutation, and return the
   final cost for `ModelDesc` training.
5. **Create the optimizer once.** `optimizer()` must return a
   `tf.train.Optimizer`. If using scheduled learning rates, create a named,
   non-trainable variable such as `learning_rate` and target it from callbacks.
6. **Choose the trainer by topology.** Start with `SimpleTrainer` for CPU or one
   local GPU. Use synchronized multi-GPU trainers for data-parallel SGD, async
   trainers for intentionally asynchronous updates, and Horovod/BytePS only when
   the launcher, dependency, and log-directory behavior are controlled.
7. **Set `steps_per_epoch` deliberately.** Tensorpack epochs mainly schedule
   callbacks. If input size is not known, set `TrainConfig(steps_per_epoch=...)`.
   For multi-GPU, remember each GPU consumes one input batch, so total batch size
   is per-tower batch times the number of towers.
8. **Add callbacks and monitors.** Defaults already include moving summaries,
   progress, merged summaries, update ops, TensorBoard event writing, JSON
   history, and scalar printing. Add model saving, validation inference,
   hyperparameter schedules, best-checkpoint savers, or custom callbacks as
   needed.
9. **Respect initialization/resume ownership.** Put checkpoint or `.npz` loading
   in `TrainConfig(session_init=...)` or `AutoResumeTrainConfig`; route variable
   inspection/export details to inference-export.
10. **Bound verification.** For a quick Tensorpack sanity check, run the bundled
    helper with fake data and a temporary log directory. Do not claim benchmark
    reproduction from the smoke helper.

## Bundled smoke helper

The helper [scripts/minimal_training_smoke.py](scripts/minimal_training_smoke.py)
is a safe, fake-data training script adapted for the generated skill tree. It
has no network or dataset dependency and is intended for parser/help checks or a
very short one-epoch run:

```bash
python scripts/minimal_training_smoke.py --workdir /tmp/tensorpack-smoke --steps-per-epoch 2 --max-epoch 1
```

Use it to demonstrate the shape of a Tensorpack `ModelDesc`, `TrainConfig`,
callbacks, summaries, and trainer launch. Do not use it as evidence that a
real dataset, GPU backend, Horovod, or paper benchmark is reproducible.

## Quick answer patterns

- **"How do I start a model?"** Point to the ModelDesc quickstart in
  [references/workflows.md](references/workflows.md#minimal-modeldesc--trainconfig-quickstart)
  and explain `inputs()`, `build_graph()`, and `optimizer()`.
- **"Which trainer for N GPUs?"** Use the trainer matrix in
  [references/workflows.md](references/workflows.md#trainer-selection) and the
  API signatures in [references/api-reference.md](references/api-reference.md#trainers-and-launch).
- **"Why is validation/checkpoint missing?"** Check callback ordering and
  monitor names in [references/workflows.md](references/workflows.md#callbacks-monitors-and-summaries),
  then use [references/troubleshooting.md](references/troubleshooting.md#callbacks-monitors-and-validation).
- **"Why did multi-GPU change my epoch semantics?"** Explain per-tower batches
  and `steps_per_epoch`; use
  [references/troubleshooting.md](references/troubleshooting.md#gpu-and-multi-gpu-semantics).
- **"Can I run the ResNet/FasterRCNN/GAN/RL example?"** Read
  [references/example-recipes.md](references/example-recipes.md) and surface
  required data, optional dependencies, backend needs, and verification status.

## Known limits

- This sub-skill documents GPU and distributed trainers from API/source evidence
  but the generated Tensorpack skill pass used CPU verification as the required
  backend. Treat GPU, Horovod, BytePS, and large-dataset recipes as documented
  but not smoke-verified unless the user supplies matching hardware and data.
- Tensorpack is TF1-graph-oriented even when installed with a TF2 package. Use
  `tensorpack.tfv1` / `tf.compat.v1` style graph code and disable eager execution
  before graph construction when needed.
- Example-family commands are catalogs for adaptation. They are not bundled as
  runnable dependencies and they require the stated datasets/backends.
