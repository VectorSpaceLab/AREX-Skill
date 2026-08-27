---
name: training-and-persistence
description: "Train, evaluate, predict, save, restore, and debug TFLearn models
  with DNN, Trainer, TrainOp, Evaluator, callbacks, validation, TensorBoard,
  checkpoints, weights, and variable-scope restore mapping."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Persistence

Use this sub-skill when the task is about running a TFLearn model after the
network graph has been built: fitting arrays or feed dictionaries, evaluating
metrics, predicting outputs, checkpointing, restoring into compatible or renamed
scopes, inspecting layer weights, or diagnosing failed training/persistence.

## Load This For

- `tflearn.DNN.fit`, `predict`, `evaluate`, `save`, `load`, `get_weights`, or
  `set_weights` workflows.
- Multi-input or multi-target fitting where list ordering or named feed
  dictionaries must be correct.
- Lower-level TensorFlow graph training with `tflearn.TrainOp`,
  `tflearn.Trainer`, and `tflearn.Evaluator`.
- Validation splits/sets, `snapshot_epoch`, `snapshot_step`, `checkpoint_path`,
  `best_checkpoint_path`, `max_checkpoints`, `run_id`, and TensorBoard log
  directories.
- Checkpoint stem/file confusion, missing `input_data` or `regression`, empty
  train-op collections, graph/session reuse bugs, and scope-renamed restores
  with `scope_for_restore` or `variable_name_map`.

## Do Not Use This For

- Choosing or cataloging layer functions, activations, losses, metrics, or merge
  operators in depth. Use the layer/operator sub-skill for that.
- Loading datasets, CSV/text/image preprocessing, sequence padding, or data
  augmentation design. Use the data/input-pipeline sub-skill for that.
- Long image, NLP, reinforcement-learning, or recipe-selection guidance. Use
  the advanced-recipe sub-skill when a task is primarily about model family
  choice rather than training mechanics.

## Quick Start

1. Use a TensorFlow 1.x-compatible runtime. The verified stack for this skill is
   TFLearn 0.5.0 with TensorFlow 1.15.5 and NumPy 1.18.5. TensorFlow 2.x modern
   imports are not compatible with this checkout without additional porting.
2. Build a fresh graph for each independent model in scripts/notebooks:
   `with tf.Graph().as_default(): ...` or `tf.reset_default_graph()` before a
   rebuild.
3. Include at least one `tflearn.input_data(...)` layer and one
   `tflearn.regression(...)` estimator before constructing `tflearn.DNN(...)`.
4. Prefer named dictionaries for non-trivial feeds:
   `model.fit({'input': X}, {'target': Y}, ...)`. Lists are matched by input and
   target creation order.
5. Put `tensorboard_dir`, `checkpoint_path`, manual save stems, and smoke-test
   `--model-dir` under an explicit experiment/temp directory, not an implicit
   current working directory.

Run the bundled no-network smoke from this sub-skill directory:

```bash
python scripts/tiny_dnn_regression_smoke.py --help
python scripts/tiny_dnn_regression_smoke.py --epochs 5
python scripts/tiny_dnn_regression_smoke.py --epochs 5 --model-dir /tmp/tflearn-smoke
```

Expected smoke output includes a prediction shape and either a checkpoint stem
or `<not saved>` when `--no-save` is used.

## References

- [API reference](references/api-reference.md): signatures, input forms,
  callbacks, `DNN`, `Trainer`, `TrainOp`, `Evaluator`, and weights APIs.
- [Workflows](references/workflows.md): ready-to-adapt training, validation,
  prediction, multi-input/multi-target, custom `Trainer`, and callback patterns.
- [Checkpointing and weights](references/checkpointing.md): checkpoint stems,
  snapshots, manual save/load, `weights_only`, layer variables, and scope
  mapping.
- [Troubleshooting](references/troubleshooting.md): concrete error signals and
  fixes for feeds, graph/session reuse, validation, TensorBoard, and restore
  failures.

## Operating Checklist

Before telling a user a training or restore workflow is ready, check:

- Graph isolation: one fresh graph per independent model rebuild.
- Collections: `tf.GraphKeys.INPUTS`, `TARGETS`, and `TRAIN_OPS` are populated
  as expected.
- Feed contract: list ordering is intentional, or dictionaries use known input
  and target names/Tensor keys.
- Runtime paths: checkpoint/log directories are explicit and writable.
- Validation: `validation_set`/`val_feed_dicts` match the same feed form as
  training data; `validation_batch_size` is set when validation memory differs.
- Restore contract: checkpoint stem is used, graph architecture and variable
  names match, or `scope_for_restore`/`variable_name_map` is supplied.
- Persistence proof: at least one prediction/evaluation runs before and after
  `save`/`load` when the task depends on restored weights.
