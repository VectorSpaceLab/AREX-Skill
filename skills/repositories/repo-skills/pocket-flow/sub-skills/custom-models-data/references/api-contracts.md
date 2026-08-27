# API Contracts for Custom PocketFlow Models and Data

PocketFlow is a TensorFlow 1.x framework. Custom integrations are ordinary Python modules loaded from an active PocketFlow checkout; there is no package installation entry point for custom tasks. The learner receives one `ModelHelper` object and borrows its dataset, forward-pass, loss, learning-rate, warm-start, and evaluation hooks.

## Dataset contract

Subclass `AbstractDataset` for file-backed datasets or mirror its contract when overriding `build()` for in-memory datasets.

### Constructor

`AbstractDataset.__init__(is_train)` establishes the shared state:

- `is_train`: whether this object describes the training subset.
- `enbl_shard`: true only when `is_train` and `FLAGS.enbl_multi_gpu`; file-backed datasets should shard filenames through the multi-GPU wrapper before reading.
- Placeholder attributes expected from subclasses: `file_pattern`, `dataset_fn`, `parse_fn`, and `batch_size`.

A dataset subclass should usually:

1. Call `super(<DatasetClass>, self).__init__(is_train)`.
2. Resolve `data_dir` from `FLAGS.data_disk`:
   - `local`: require `FLAGS.data_dir_local`.
   - `hdfs`: require both `FLAGS.data_hdfs_host` and `FLAGS.data_dir_hdfs`.
3. Set train/eval `file_pattern` and `batch_size`.
4. Set `dataset_fn` to a TensorFlow dataset reader, such as `tf.data.FixedLengthRecordDataset` or `tf.data.TFRecordDataset`.
5. Set `parse_fn` so each record becomes the tensors expected by the model helper.

### Shared dataset flags

`AbstractDataset` defines shared path and pipeline flags:

- `data_disk`: `local` or `hdfs` inside the TensorFlow input pipeline.
- `data_hdfs_host`, `data_dir_local`, `data_dir_hdfs`: resolved by launch helpers from `path.conf`.
- `cycle_length`, `nb_threads`, `buffer_size`, `prefetch_size`: TensorFlow input-pipeline controls.

Dataset modules define task-specific flags such as `nb_classes`, `nb_smpls_train`, `nb_smpls_val`, `nb_smpls_eval`, `batch_size`, and `batch_size_eval`. Keep these names aligned with learners that compute iteration counts from sample counts and batch sizes.

### `build()` behavior

The inherited `build(enbl_trn_val_split=False)` method for file-backed datasets:

1. Lists files matching `self.file_pattern`.
2. Optionally shards the filenames for multi-GPU training.
3. Builds a `tf.data.Dataset` using `self.dataset_fn`.
4. Maps `self.parse_fn`.
5. Optionally splits training data into train/validation iterators when `is_train` and `enbl_trn_val_split` are true.
6. Applies `tf.contrib.data.shuffle_and_repeat`, batches, prefetches, and returns one-shot iterators.

Override `build()` only when the source is not naturally file-backed, such as the Fashion-MNIST-style NumPy/gzip example. Even then, preserve the return forms: either one iterator or `(iterator_trn, iterator_val)` when training/validation splitting is enabled.

## Iterator output contracts

### Classification

For ordinary image classification helpers, each iterator yields:

- `images`: a tensor, usually NHWC (`channels_last`) after preprocessing.
- `labels`: a one-hot label tensor of width `FLAGS.nb_classes`.

The helper's `calc_loss(labels, outputs, trainable_vars)` can then use softmax cross-entropy and return an accuracy metric.

### Detection or label-aware forward passes

Object detection helpers may yield image dictionaries plus packed annotation tensors. If `forward_train()` needs labels or packed objects, initialize the helper with `forward_w_labels=True` and implement a compatible signature. Full-precision training explicitly checks this flag. Many compression learners call `forward_train(images)` directly, so verify learner compatibility before selecting a compression learner for a label-aware helper.

## ModelHelper contract

`AbstractModelHelper.__init__(data_format, forward_w_labels=False)` stores:

- `data_format`: normally `channels_last` or `channels_first`.
- `forward_w_labels`: whether full-precision training passes labels/objects into `forward_train()`.

Do not create TensorFlow operations in the `ModelHelper` constructor. It is acceptable to instantiate dataset objects there; graph operations should be created later by `build_dataset_*()` and `forward_*()` inside the learner's TensorFlow graph.

A concrete `ModelHelper` must implement:

| Method/property | Required behavior |
| --- | --- |
| `build_dataset_train(enbl_trn_val_split=False)` | Return the train iterator, or train/validation iterators when requested. |
| `build_dataset_eval()` | Return the evaluation iterator. |
| `forward_train(inputs, labels=None)` | Build the training graph and return logits or a structured output dict. Omit `labels` unless `forward_w_labels=True`. |
| `forward_eval(inputs)` | Build the evaluation graph; avoid training-only ops such as augmentation-specific behavior or batch-norm update side effects. |
| `calc_loss(labels, outputs, trainable_vars)` | Return `(loss, metrics)` where `metrics` is a dict of TensorFlow scalar tensors. |
| `setup_lrn_rate(global_step)` | Return `(lrn_rate, nb_iters)` for the learner loop. Scale batch size by the multi-GPU wrapper when multi-GPU is enabled. |
| `warm_start(sess)` | Optional; initialize from a backbone/pretrained checkpoint. Default is a no-op. |
| `dump_n_eval(outputs, action)` | Optional; dump predictions and run evaluation for tasks such as detection. Default is a no-op. |
| `model_name` | String used in checkpoint/archive naming. |
| `dataset_name` | String used in checkpoint/archive naming. |

The learner forms pre-trained model archive names from `model_name` and `dataset_name` as `models_<model_name>_at_<dataset_name>.tar.gz`. Keep these names stable once checkpoints exist.

## Run script contract

A run script should follow the `nets/*_run.py` pattern:

- Import TensorFlow 1.x and `create_learner`.
- Import the task's `ModelHelper`.
- Define common flags: `log_dir`, `enbl_multi_gpu`, `learner`, `exec_mode`, and `debug`.
- Create a `tf.summary.FileWriter(FLAGS.log_dir)`.
- Instantiate `model_helper = ModelHelper()`.
- Create `learner = create_learner(sm_writer, model_helper)`.
- Dispatch `learner.train()` for `exec_mode == 'train'` and `learner.download_model(); learner.evaluate()` for `exec_mode == 'eval'`.
- End with `tf.app.run()`.

Run script filenames also drive path-key lookup for launchers. Use `nets/<model_key>_at_<dataset_key>_run.py` and keep `<dataset_key>` alphanumeric to match PocketFlow's path argument parser.

## Data format rules

- Valid values are `channels_last` and `channels_first`.
- Dataset parsers normally emit `channels_last` images. If the model uses `channels_first`, transpose from NHWC to NCHW before calling layers that expect NCHW.
- Some built-ins assert `channels_last` only; MobileNet is one such helper.
- Watch for stale snippets that use `channel_first` without the final `s`; PocketFlow's current helpers expect `channels_first`.

## TensorFlow flag hygiene

TensorFlow 1.x `tf.app.flags` are process-global. Avoid importing multiple custom task modules that define the same flag names in one Python process. Prefer one task helper per run script, or give experimental flags unique names.
