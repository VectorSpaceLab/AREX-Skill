# Model Overview

This sub-skill covers the TF1 dense and sparse trainers plus the shared helper modules that define model bodies, optimizer selection, checkpoint restore, and SavedModel export.

## Trainer-to-model map

| Trainer | Input layout | Supported models | Training style | Export style |
| --- | --- | --- | --- | --- |
| Dense trainer | dense vectors from CSV or TFRecords | `dnn`, `lr`, `wide_and_deep`, `customized`, `cnn`, `customized_cnn`, `lstm`, `bidirectional_lstm`, `gru` | `tf.data` pipelines | `savedmodel` mode via shared export helper |
| Sparse trainer | sparse ids and values from TFRecords | `dnn`, `lr`, `wide_and_deep`, `customized` | `tf.data` pipelines over sparse TFRecords | `save_model` mode via shared export helper |
| Dense queue trainer | dense vectors from CSV or TFRecords | `dnn`, `lr`, `wide_and_deep`, `customized`, `cnn` | queue runners + `tf.train.Supervisor` | `savedmodel` mode with queue-era signature names |
| Distributed dense trainer | dense TFRecords | simple two-layer dense model only | ps/worker cluster with queue runners | checkpointed training only |

## Dense model families

| Model | What it does | Input shape notes | Best fit | Watch out for |
| --- | --- | --- | --- | --- |
| `dnn` | Fully connected network with depth from `dnn_struct` | Any flat feature vector that matches `feature_size` | Default dense classification or regression | `dnn_struct` must contain at least one hidden layer size |
| `lr` | Linear classifier/regressor | Any flat feature vector | Simple baseline | `wide_and_deep` adds this path to the DNN path |
| `wide_and_deep` | Sum of `lr` and `dnn` logits | Any flat feature vector | Mixed linear + deep baseline | Make sure the label encoding matches the chosen loss |
| `customized` | Fixed 128-32-8 stack | Any flat feature vector | Quick predefined dense stack | Dropout only activates when the flag is on and the graph is in training mode |
| `cnn` | 3x3 convolutional toy network | Current source reshapes to 3x3, so `feature_size` must match 9 | Tiny image-like toy inputs | The reshape is hard-coded; bad feature counts fail fast |
| `customized_cnn` | Three-layer CNN for larger images | Current source reshapes to 512x512 and uses `train_batch_size` in the reshape | Dense image-style inputs | `feature_size` should be 512*512 and batch size must match the reshape assumptions |
| `lstm` | 3-step sequence model | Current source reshapes to 3x3 | Small sequence-shaped toy inputs | TF1 `tf.contrib.rnn` required |
| `bidirectional_lstm` | Bidirectional 3-step sequence model | Current source reshapes to 3x3 | Sequence toy inputs | TF1 `tf.contrib.rnn` required |
| `gru` | GRU sequence model | Current source reshapes to 3x3 | Sequence toy inputs | TF1 `tf.contrib.rnn` required |

## Sparse model families

| Model | What it does | Input shape notes | Best fit | Watch out for |
| --- | --- | --- | --- | --- |
| `dnn` | Sparse embedding lookup followed by dense stack | `ids` and `values` sparse tensors with `feature_size` as the embedding width | Default sparse classification | `feature_size` is the vocabulary or embedding width, not the number of nonzero values |
| `lr` | Sparse logistic regression | Sparse ids and values | Baseline sparse model | The current source references `FLAGS.input_units` in the LR branch even though the flags define `feature_size`; treat this branch as fragile |
| `wide_and_deep` | Sum of sparse linear and DNN logits | Sparse ids and values | Mixed sparse baseline | Both branches must agree on label size and feature width |
| `customized` | Fixed 128-32-8 sparse stack | Sparse ids and values | Predefined sparse stack | Dropout and batch norm behave like the dense variant |

## Optimizers

`util.get_optimizer_by_name` and the trainer flag validators accept the same optimizer family:

- `sgd`
- `adadelta`
- `adagrad`
- `adam`
- `ftrl`
- `rmsprop`

The helper falls back to gradient descent if called directly with an unknown name, but the trainer flags reject unknown values.

## Losses and scenarios

| Trainer | Supported loss names | Scenario flag | Notes |
| --- | --- | --- | --- |
| Dense | `sparse_cross_entropy`, `cross_entropy`, `mean_square` | `classification` or `regression` | `sparse_cross_entropy` is the default; `mean_square` is the regression branch |
| Sparse | Sparse cross entropy only in the current path | Classification only | The sparse trainer does not expose a separate regression scenario flag |

## Helper APIs worth remembering

| Helper | Signature | Role |
| --- | --- | --- |
| `util.get_optimizer_by_name` | `(optimizer_name, learning_rate)` | Returns the selected TF1 optimizer |
| `util.restore_from_checkpoint` | `(sess, saver, checkpoint_file_path)` | Restores the latest checkpoint if it exists |
| `util.save_model` | `(model_path, model_version, sess, signature_def_map, is_save_graph=False)` | Writes a SavedModel under `model_path/model_version` |
| `model.compute_softmax_and_accuracy` | `(logits, labels)` | Dense train/validation accuracy helper |
| `model.compute_auc` | `(softmax_op, label_op, label_size)` | Dense AUC helper |

## Export and inference outputs

- Dense current export builds a SavedModel with `keys` and `features` inputs.
- Dense current export adds `prediction` and `softmax` outputs, plus a custom secondary signature in the source.
- Sparse export builds a SavedModel with `keys`, `indexs`, `ids`, `values`, and `shape` inputs.
- Sparse export returns `prediction` and `softmax` outputs.
- Queue-era dense export uses `output_keys`, `output_prediction`, and `output_softmax` graph names.

## Shape reminders

- Dense `cnn` and the RNN models are only safe when the flat input size matches the hard-coded reshape.
- Dense `customized_cnn` is the only path that expects a very large flat image vector.
- Sparse `feature_size` is the embedding width / vocabulary width, while the `ids` and `values` tensors describe the sparse coordinates and weights.
