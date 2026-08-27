# CLI Reference

This reference collects the user-facing flag names that matter for training, export, and inference. It also records the README-era aliases that still appear in examples and the command builder's normalization rules.

## Dense trainer: current flags

### Mode and model control

| Flag | Default | Meaning |
| --- | --- | --- |
| `mode` | `train` | `train`, `savedmodel`, or `inference` |
| `scenario` | `classification` | `classification` or `regression` |
| `loss` | `sparse_cross_entropy` | `sparse_cross_entropy`, `cross_entropy`, or `mean_square` |
| `model` | `dnn` | `dnn`, `lr`, `wide_and_deep`, `customized`, `cnn`, `customized_cnn`, `lstm`, `bidirectional_lstm`, or `gru` |
| `dnn_struct` | `128 32 8` | Hidden-layer sizes for `dnn` |

### Data flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `file_format` | `tfrecords` | `tfrecords` or `csv` |
| `train_files` | `./data/cancer/cancer_train.csv.tfrecords` | Comma-separated or glob-style training files |
| `validation_files` | `./data/cancer/cancer_test.csv.tfrecords` | Validation files |
| `feature_size` | `9` | Flat feature width |
| `label_size` | `2` | Label count |
| `inference_data_file` | `./data/cancer/cancer_test.csv` | CSV inference data |
| `inference_result_file` | `./inference_result.txt` | Prediction output file |

### Optimization and training flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `optimizer` | `adagrad` | `sgd`, `adadelta`, `adagrad`, `adam`, `ftrl`, `rmsprop` |
| `learning_rate` | `0.01` | Base learning rate |
| `epoch_number` | `100` | Epoch count; non-positive means indefinite repeat in the source path |
| `train_batch_size` | `64` | Training batch size |
| `validation_batch_size` | `64` | Validation batch size |
| `enable_bn` | `False` | Batch normalization |
| `enable_dropout` | `False` | Dropout |
| `dropout_keep_prob` | `0.5` | Dropout keep probability |
| `enable_lr_decay` | `False` | Exponential learning-rate decay |
| `lr_decay_rate` | `0.96` | Decay factor |
| `steps_to_validate` | `10` | Metric and checkpoint frequency |
| `enable_benchmark` | `False` | Skip extra validation work in benchmark mode |
| `resume_from_checkpoint` | `False` | Restore the latest checkpoint before training |

### Path flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `checkpoint_path` | `./checkpoint/` | Checkpoint directory |
| `output_path` | `./tensorboard/` | TensorBoard event directory |
| `model_path` | `./model/` | SavedModel export directory |
| `model_version` | `1` | Export subdirectory name |

## Sparse trainer: current flags

### Mode and model control

| Flag | Default | Meaning |
| --- | --- | --- |
| `mode` | `train` | `train`, `save_model`, `inference`, or `inference_with_tfrecords` |
| `model` | `dnn` | `dnn`, `lr`, `wide_and_deep`, or `customized` |
| `model_network` | `128 32 8` | Hidden-layer sizes for the sparse DNN path |
| `label_type` | `int` | `int` or `float` |

### Data flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `train_files` | `./data/a8a/a8a_train.libsvm.tfrecords` | Sparse training TFRecords |
| `validation_files` | `./data/a8a/a8a_test.libsvm.tfrecords` | Sparse validation TFRecords |
| `feature_size` | `124` | Embedding width / vocabulary width |
| `label_size` | `2` | Label count |
| `inference_test_file` | `./data/a8a_test.libsvm` | LibSVM inference input |
| `inference_result_file` | `./inference_result.txt` | Prediction output file |
| `saved_model_path` | `./sparse_saved_model/` | Saved-model related path kept in the flag set |

### Optimization and training flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `learning_rate` | `0.01` | Base learning rate |
| `epoch_number` | `10` | Epoch count |
| `batch_size` | `1024` | Legacy batch-size flag retained in the source |
| `train_batch_size` | `64` | Training batch size used by the current tf.data path |
| `validation_batch_size` | `64` | Validation batch size used by the current tf.data path |
| `validate_batch_size` | `1024` | Legacy validation batch-size flag retained in the source |
| `batch_thread_number` | `1` | Reader thread count |
| `min_after_dequeue` | `100` | Queue-style buffer hint kept for compatibility notes |
| `optimizer` | `adagrad` | Same optimizer family as the dense trainer |
| `steps_to_validate` | `10` | Metric frequency |
| `enable_bn` | `False` | Batch normalization |
| `enable_dropout` | `False` | Dropout |
| `dropout_keep_prob` | `0.5` | Dropout keep probability |
| `enable_lr_decay` | `False` | Exponential learning-rate decay |
| `lr_decay_rate` | `0.96` | Decay factor |
| `benchmark_mode` | `False` | Skip extra work in benchmark mode |

### Path flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `checkpoint_path` | `./sparse_checkpoint/` | Checkpoint directory |
| `output_path` | `./sparse_tensorboard/` | TensorBoard event directory |
| `model_path` | `./sparse_model/` | SavedModel export directory |
| `model_version` | `1` | Export subdirectory name |

## Legacy queue trainer: useful aliases

The queue-based dense trainer keeps older flag names that still appear in README examples.

| Older flag | Current dense trainer flag | Notes |
| --- | --- | --- |
| `train_file` | `train_files` | README-era dense example alias |
| `validate_file` | `validation_files` | README-era dense example alias |
| `input_file_format` | `file_format` | README-era dense example alias |
| `model_network` | `dnn_struct` | README-era dense example alias |
| `batch_size` | `train_batch_size` | Queue script uses `batch_size`; current dense trainer uses `train_batch_size` |
| `validate_batch_size` | `validation_batch_size` | Queue script uses `validate_batch_size`; current dense trainer uses `validation_batch_size` |
| `step_to_validate` | `steps_to_validate` | README typo/older naming |
| `optmizier` | `optimizer` | README typo/older naming |

## Dense trainer: README-era example names

The README still shows the following names in older snippets:

- `train_file`
- `validate_file`
- `input_file_format`
- `model_network`
- `batch_size`
- `validate_batch_size`
- `step_to_validate`
- `optmizier`

Use the command builder to normalize those names into the current dense flag set.

## Mode reminders

| Trainer | Training mode | Export mode | Inference mode |
| --- | --- | --- | --- |
| Dense current | `train` | `savedmodel` | `inference` |
| Dense queue | `train` | `savedmodel` | `inference` |
| Sparse current | `train` | `save_model` | `inference` or `inference_with_tfrecords` |

## Practical notes

- Dense and sparse trainers register `tf.app.flags` during import, so the flag surface is not safe to mix in one Python process.
- Dense current uses `train_files` and `validation_files`; if a command still says `train_file`, it is using the older queue-style naming.
- The bundled command builder accepts both hyphenated and underscore spellings for the common flags, so pasting source examples is usually safe.
- Sparse current does not offer a `scenario` flag; classification is implied by the loss path.
- Sparse LR is still flagged here because it exists in the source, but the model overview documents why that branch is fragile.
