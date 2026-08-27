# Workflows

This reference collects the common training, export, inference, and TensorBoard flows for the dense and sparse trainers. It stays close to the source behavior while keeping the sub-skill router-like.

## Dense training

Use the dense trainer when the input is a flat feature vector and you want the current `tf.data` pipeline.

Typical steps:

1. Choose the model family and data layout.
2. Make sure `feature_size` matches the flat vector width.
3. Choose `scenario` and `loss` together when you need regression.
4. Let the trainer write checkpoints under `checkpoint_path` and event files under `output_path`.
5. Export a SavedModel after training or in a separate `savedmodel` run.

Recommended command-builder usage:

```bash
python scripts/build_training_command.py \
  --target dense \
  --mode train \
  --train-files ./data/cancer/cancer_train.csv.tfrecords \
  --validation-files ./data/cancer/cancer_test.csv.tfrecords \
  --feature-size 9 \
  --label-size 2 \
  --model dnn \
  --optimizer adagrad
```

For dense regression, add `--scenario regression` and `--loss mean_square` so the loss branch matches the intended task.

## Dense export

A successful dense training run writes checkpoints first and then exports a SavedModel under `model_path/model_version`.

Important points:

- `savedmodel` mode restores the latest checkpoint before export.
- The export directory must not already exist at the target version.
- Dense export exposes `keys` plus `features` inputs and prediction outputs in the SavedModel signature map.

Use a fresh `model_version` when you want to keep older exports side by side.

## Dense inference

Dense inference loads the latest checkpoint and runs prediction on a CSV file.

Workflow reminders:

- The default inference file is a CSV with features followed by the label column.
- `feature_size` must match the number of feature columns.
- The script writes probability rows to `inference_result_file`.

If inference fails with a shape error, check the feature width before checking the checkpoint.

## Sparse training

Use the sparse trainer when the input is a sparse TFRecords representation of ids and values.

Typical steps:

1. Make sure the sparse TFRecords contain `ids`, `values`, and `label`.
2. Set `feature_size` to the embedding width / vocabulary width.
3. Choose one of the sparse model families: `dnn`, `lr`, `wide_and_deep`, or `customized`.
4. Train under the current sparse `tf.data` path.
5. Export with `save_model` after a checkpoint exists.

Recommended command-builder usage:

```bash
python scripts/build_training_command.py \
  --target sparse \
  --mode train \
  --train-files ./data/a8a/a8a_train.libsvm.tfrecords \
  --validation-files ./data/a8a/a8a_test.libsvm.tfrecords \
  --feature-size 124 \
  --label-size 2 \
  --model dnn \
  --optimizer adagrad
```

## Sparse export

Sparse export uses `mode=save_model`.

Important points:

- The exporter still needs a restored checkpoint.
- The SavedModel is written beneath `model_path/model_version`.
- The sparse SavedModel signature expects `keys`, `indexs`, `ids`, `values`, and `shape` tensors.

If a user says `savedmodel` for the sparse trainer, they usually mean `save_model`.

## Sparse inference

Sparse inference has two flavors:

- `inference` reads the LibSVM-style text file.
- `inference_with_tfrecords` reads the sparse TFRecords representation.

Use `inference_with_tfrecords` when you want to stay inside the sparse TFRecords path and avoid manual LibSVM parsing.

## TensorBoard event reading

Use the bundled helper to inspect scalar summaries without hardcoding a private path.

```bash
python scripts/read_tensorboard_events.py \
  --event-file ./tensorboard/events.out.tfevents.* \
  --tag loss \
  --tag train_accuracy \
  --tag train_auc \
  --tag validate_accuracy \
  --tag validate_auc
```

Notes:

- If no tags are supplied, the helper prints all scalar summary values it finds.
- The source logs may expose `loss`, `loss_1`, or another tag name depending on the graph branch.
- Point the helper at the event file or the log directory, not the SavedModel export directory.

## Legacy queue notes

The queue-based dense trainer exists for older queue-runner workflows and README-era flag names.

Use it when a user explicitly asks about:

- `train_file` / `validate_file` flag names
- queue runners or `tf.train.Supervisor`
- the older dense training style rather than the current `tf.data` path

Cautions:

- Keep the queue trainer in a separate process from the current dense trainer.
- Queue-style training uses `batch_size`, `validate_batch_size`, and `train_file_format` naming.
- The queue path is useful for reference and compatibility, but the current dense trainer is the cleaner default.

## Distributed dense notes

The distributed dense trainer is a ps/worker example rather than the main training path.

Use it only when the user explicitly wants distributed TensorFlow behavior.

Cautions:

- Start a separate process for each ps or worker role.
- Parameterize `ps_hosts`, `worker_hosts`, `job_name`, and `task_index` per process.
- The source notes expect ps tasks to run on CPU and worker tasks to be able to use GPUs.
- The source file hard-codes data paths, so treat it as a reference for cluster shape and not as a flexible general-purpose trainer.

## Recovery order when a run fails

1. Verify the flag names with `references/cli-reference.md`.
2. Verify the model and loss choice with `references/model-overview.md`.
3. Check checkpoint and export paths.
4. Check feature width or sparse tensor shape.
5. Use `scripts/read_tensorboard_events.py` only after the run writes event files.
