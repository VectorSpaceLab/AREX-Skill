# Training and Prediction Operations

The repository models are standalone TensorFlow 1.x scripts. They are not exposed as an importable package API. Treat every train/predict script as a script with relative-path assumptions, TensorFlow 1.x flags, and external artifacts.

## Environment assumptions

Use language and tooling consistent with the repository era:

- Python 3.7 is the safest target for patched Python 3 runs; some files still contain Python 2 idioms such as `reload(sys)` and `sys.setdefaultencoding`.
- TensorFlow 1.x is required for `tf.placeholder`, `tf.Session`, `tf.app.flags`, `tf.contrib`, and graph collections.
- TFLearn examples require a TFLearn version compatible with the TensorFlow 1.x runtime.
- Common data dependencies include `h5py`, `pickle`, `numpy`, `tflearn.data_utils`, optional `word2vec`, optional `gensim`, and sometimes `numba`.

Do not assume TensorFlow 2.x or Python 3.13 works. Disabling eager execution is not enough when a script depends on `tf.contrib` or old TFLearn internals.

## Required artifacts

Full training and prediction usually need artifacts that are not bundled with this generated skill:

| Artifact | Used by | Notes |
| --- | --- | --- |
| HDF5 cache | fastTextB, TextCNN, BERT multi-label, some utility paths | Expected keys include training, validation, and test arrays such as `train_X`, `train_Y`, `vaild_X`, `valid_Y`, `test_X`, and `test_Y`. |
| Vocabulary/label pickle | fastTextB, TextCNN, BERT multi-label | Usually contains `word2index` and `label2index`; all label dimensions must match checkpoint/model dimensions. |
| Raw token-label text | TextRNN, RCNN, HAN legacy paths | Lines follow a token sequence plus `__label__...` labels; preprocessing routes are older and more fragile than HDF5 paths. |
| Checkpoint directory | All trained models | Prediction requires a `checkpoint` state file and matching `model.ckpt-*` files. |
| Word2vec binary | Optional embeddings for classic models | Only load when `use_embedding` is true and `embed_size` matches the binary vectors. |
| BERT vocab/config/checkpoint | BERT prediction or fine-tuning | Vocab size, hidden size, sequence length, and checkpoint variables must be compatible. |

If any artifact is missing, do not claim the model is immediately runnable. First decide whether to download/generate data, use a tiny synthetic graph check, or narrow the task to code inspection.

## Common training pattern

Most classic training scripts follow the same graph/session skeleton:

1. Define `tf.app.flags` for cache paths, checkpoint directory, learning rate, batch size, sequence length, embedding size, epoch count, and multi-label flags.
2. Load data and label/vocabulary mappings.
3. Create `tf.ConfigProto()` and set `gpu_options.allow_growth=True`.
4. Instantiate the model class with dimensions derived from the cache or flags.
5. Create `tf.train.Saver()`.
6. Restore from `ckpt_dir` if a checkpoint exists; otherwise initialize variables and optionally assign pretrained embeddings.
7. Iterate minibatches, feed placeholders, run `[loss, train_op]`, periodically evaluate, and save checkpoints.

Before running a full loop, perform a tiny graph build with the intended dimensions and check placeholder compatibility.

## fastTextB operations

Training uses the multi-label model with:

- `sentence`: padded integer ids with shape `[batch, sentence_len]`.
- `labels_l1999`: dense multi-hot targets with shape `[batch, label_size]`.
- `ckpt_dir`: a directory containing or receiving TensorFlow checkpoint state.
- Optional `use_embedding` and word2vec binary assignment.

Operational notes:

- The active loss is sigmoid multi-label cross entropy; top-k prediction reads the largest logits.
- The HDF5/pickle cache must exist before training starts.
- The provided prediction script is stale in places and references older single-label module names. Prefer adapting the multi-label model and the training script's cache loader rather than using it blindly.

## TextCNN operations

Training uses:

- `input_x`: `[batch, sentence_len]`.
- `input_y_multilabel`: `[batch, num_classes]` when `multi_label_flag=True`.
- `dropout_keep_prob`: `0.8` during training and `1.0` during evaluation/prediction.
- `is_training_flag`: true for batch-norm update collection during training, false for evaluation/prediction.
- Filter sizes `[6, 7, 8]` in the main training script.

The script restores an existing checkpoint if present, otherwise initializes. If `use_embedding=True`, it assigns external word vectors into the embedding variable.

Prediction pattern:

1. Load exactly the vocabulary/label mapping used for training.
2. Convert tokens to ids and pad to the training `sentence_len`.
3. Instantiate TextCNN with the same `filter_sizes`, `num_filters`, `num_classes`, `vocab_size`, and `embed_size`.
4. Restore the checkpoint.
5. Feed `input_x`, `dropout_keep_prob=1.0`, and `is_training_flag=False`.
6. Convert logits or sigmoid probabilities to top-k labels.

## TextRNN operations

TextRNN scripts are mostly single-label:

- They load raw text-label data through legacy utilities.
- They pad token ids to `sequence_length`.
- Labels are sparse integer ids fed to `input_y`.
- Loss is sparse-softmax cross entropy.
- Optional word2vec assignment is common.

Do not import model files casually: some invoke their toy `test()` at module import time. If you need inspection, patch a local copy or use a controlled subprocess with a timeout.

## TextRCNN operations

RCNN scripts support both single-label and multi-label modes, but variants differ in constructor order and batch handling.

Checklist before training or prediction:

1. Confirm which RCNN class file is imported.
2. Match the constructor signature exactly, especially the position of `batch_size`.
3. Keep runtime batch size consistent with any fixed-batch context variables.
4. For multi-label mode, feed `input_y_multilabel`; for single-label, feed `input_y`.
5. Set `dropout_keep_prob=0.5` or similar during training and `1.0` for evaluation/prediction.

Prediction should restore a checkpoint, pad input to the same sequence length, run logits, then write top-k labels with the label-index mapping.

## Hierarchical Attention Network operations

Classic HAN expects a flattened document-like sequence:

- `sequence_length` in flags is the total flattened length.
- `num_sentences` controls the split; total length must be divisible by it.
- Each sub-sequence is encoded, attended, then combined into a document representation.
- `multi_label_flag=True` switches to sigmoid multi-label loss.

Before training:

1. Confirm whether the classic HAN model or transformer-named variant is imported under `HierarchicalAttention`.
2. Confirm `num_sentences`, total sequence length, and label shape.
3. Use the same preprocessing split at prediction time.
4. Use checkpoint directories that correspond to the active variant.

The separate multi-task HAN model has a different target contract with several classification heads and one regression-like output. Do not substitute it for the p1 multi-label classifier without matching labels.

## BERT operations

The multi-label BERT training path builds BERT from token-id caches rather than using high-level BERT estimators:

- `input_ids`: `[batch, max_seq_length]`, with `[CLS]` inserted at the beginning.
- `input_mask`: `[batch, max_seq_length]`, set to zero after the first padding token.
- `segment_ids`: `[batch, max_seq_length]`.
- `label_ids`: `[batch, num_labels]` multi-hot labels.
- `is_training`: boolean placeholder controlling dropout.

The repository's multi-label BERT head uses sigmoid probabilities. Its utility function picks labels by threshold and falls back to argmax when no probability exceeds the threshold.

For pretrained BERT-style prediction, also require:

- BERT config JSON.
- Vocabulary file compatible with tokenization.
- Checkpoint variables matching the config.
- A stable tokenizer and sequence truncation policy.

The online prediction runner demonstrates single-example restore and prediction, but it is a single-label softmax sequence-pair pattern. Convert it carefully for multi-label use.

## Legacy TFLearn operations

TFLearn examples are useful for syntax and smoke demonstrations only:

- Fully connected toy classifier: random `[batch, 784]` features and categorical cross entropy.
- Sentence CNN: IMDB ids, embedding, `conv_1d`, `global_max_pool`, dropout, softmax.
- CIFAR CNN: image-specific and not a text model.

They may download datasets or expect local dataset caches. Keep them out of main model validation unless the task is specifically about TFLearn examples.

## Prediction output discipline

For all models:

- Use the exact vocabulary and label mapping from training.
- Match sequence length, embedding dimension, label count, model variant, and checkpoint directory.
- Use logits for top-k ranking or sigmoid probabilities for thresholded multi-label output; do not apply softmax to independent multi-label logits.
- Keep checkpoint output files separate by model family and feature set.
- Treat benchmark scores in the README as historical context, not a reproduction guarantee.
