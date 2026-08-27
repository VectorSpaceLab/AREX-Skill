# Classification Model Troubleshooting

Use this guide when graph construction, training, restoration, prediction, or shape inspection fails for the classification model families.

## TensorFlow and Python runtime failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `module 'tensorflow' has no attribute 'placeholder'` | TensorFlow 2.x imported as `tensorflow`. | Use a TensorFlow 1.x environment. A `compat.v1` shim is not enough for scripts using `tf.contrib`. |
| `module 'tensorflow' has no attribute 'contrib'` | TensorFlow 2.x or incompatible TensorFlow install. | Use TensorFlow 1.x with Python 3.7-era dependencies. |
| `tflearn` import errors | TFLearn version incompatible with TensorFlow or Python version. | Use TFLearn only in the legacy TF1 environment; do not validate main models through TFLearn. |
| `reload` or `sys.setdefaultencoding` failures | Python 2 idioms left in scripts. | Patch the script for Python 3 or avoid that path. Do not downgrade task expectations silently. |
| Graph/eager execution conflicts | TF2-style runtime or mixed imports. | Start a fresh Python process in TF1 mode and build a static graph. |

## Data and artifact failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Runtime error asking to download cache files | HDF5 or pickle cache is absent. | Provide or generate the HDF5 data cache and vocabulary/label pickle before training. |
| HDF5 key errors | Cache schema differs from the scripts. | Verify expected keys such as `train_X`, `train_Y`, `vaild_X`, `valid_Y`, `test_X`, and `test_Y`. |
| Label shape mismatch | `num_classes` does not match the label pickle or checkpoint. | Derive `num_classes` from `label2index` and use a checkpoint trained with the same label mapping. |
| Pickle loading errors | Python version or encoding mismatch. | Load with an explicit encoding when necessary, or regenerate the vocabulary/label pickle in the target runtime. |
| Word2vec assignment shape mismatch | `embed_size` differs from vector size. | Disable `use_embedding` or match `embed_size` to the external binary. |

## Model-specific traps

### fastTextB

- Active multi-label loss feeds `labels_l1999`, not the sparse `labels` placeholder.
- Prediction code in the repository is stale in places and references older module names. Adapt from the multi-label model and cache loader.
- NCE-related comments do not describe the active multi-label training path.

### TextCNN

- Use `multi_label_flag=True` for the current main multi-label script. The single-label branch references an `input_y` placeholder that is not active in the current model file.
- Feed `is_training_flag=True` while training so batch-norm update ops run; feed false for evaluation/prediction.
- `filter_sizes`, `num_filters`, `embed_size`, and `num_classes` must match the checkpoint.
- Prediction code may need repair around flags and data utility imports before it is production-safe.

### TextRNN

- Some model files call `test()` at import time. Importing them can unexpectedly start a toy training loop.
- The common model is single-label with sparse-softmax loss; do not feed multi-hot labels unless the graph was modified.
- External word2vec binaries and raw-data utilities are common prerequisites.

### TextRCNN

- Constructor order differs between RCNN variants. Inspect the class before passing positional arguments.
- Several tensors are shaped with fixed `batch_size`; prediction batches must match or the model must be refactored.
- In multi-label mode, `accuracy` may be a placeholder/fake constant; compute meaningful metrics outside the graph.
- Checkpoint directories are variant-specific and feature-set-specific.

### Hierarchical Attention Network

- Total input length must be divisible by `num_sentences`.
- The training script can shadow the classic HAN class with a transformer-named variant. Confirm the active imported class.
- The multi-task HAN model has multiple classification targets and a regression-like target; it is not drop-in compatible with the p1 classifier.
- Attention implementations are legacy and may use deprecated TensorFlow argument names such as `keep_dims`.

### BERT

- Some files import `modeling`, while the bundled BERT implementation is named differently in this repository. Fix import names before running.
- `BertConfig` dimensions must be internally consistent: `hidden_size` divisible by `num_attention_heads`, and `max_position_embeddings` at least `max_seq_length`.
- Multi-label training uses sigmoid probabilities. Do not replace with softmax unless the task is single-label.
- Online prediction code demonstrates sequence-pair softmax and may have shape assumptions that need review before reuse.
- Full-size BERT models require significant memory; no GPU verification is claimed here.

### TFLearn examples

- TFLearn examples may download IMDB or CIFAR data and are not evidence that the main models train.
- They use categorical cross entropy and softmax for toy single-label cases, not the main multi-label Zhihu loss.

## Checkpoint restoration failures

When `Saver.restore` fails:

1. Confirm the checkpoint directory contains a TensorFlow `checkpoint` state file.
2. Confirm model hyperparameters match the checkpoint: label count, vocab size, embedding size, filter sizes, hidden size, sequence length, and variant.
3. Confirm variable names did not change because a different source file or import alias was used.
4. For BERT, confirm config JSON, vocab, and checkpoint variables came from the same training run or compatible pretrained model.

## Prediction quality failures

If predictions are syntactically valid but poor:

- Confirm preprocessing uses the same vocabulary, padding length, token order, and label index mapping used in training.
- For multi-label tasks, compare thresholded sigmoid predictions versus fixed top-k logits. The repository often reports top-5-style metrics.
- Do not use softmax over independent multi-label classes.
- Inspect a small batch manually: raw token ids, non-padding mask positions, label ids, logits/probabilities, and decoded labels.

## Safe escalation path

1. Run a tiny graph-construction inspection with the bundled shape script.
2. Verify cache and checkpoint artifacts separately.
3. Run one tiny synthetic or cached minibatch, not a full epoch.
4. Only then run a normal training or prediction script with explicit checkpoint/data paths.

This sub-skill does not claim benchmark reproduction, TensorFlow 2.x support, or GPU verification.
