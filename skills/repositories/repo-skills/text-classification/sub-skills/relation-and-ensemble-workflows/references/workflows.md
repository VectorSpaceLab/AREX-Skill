# Relation, Boosting, And Ensemble Workflows

This reference distills the repo's relation-classification, TextCNN+RCNN hybrid,
boosting, and ensemble-logit patterns into self-contained operating knowledge.
It intentionally avoids depending on the original checkout at runtime.

## Runtime Assumptions

- Treat the project as a legacy TensorFlow 1.x / TFLearn script collection, not
  an installable package.
- Prefer Python 3.7-era TensorFlow 1.x compatibility when recreating graphs.
  TensorFlow 2.x removes `tf.contrib` and changes execution defaults; Python
  3.13 is not an appropriate assumption for these scripts.
- Source-style training and prediction are not immediately runnable from this
  skill alone. They usually need external Zhihu-format TSV data, vocabulary and
  label maps, pretrained word2vec embeddings, pickled/HDF5 caches, and matching
  checkpoint directories.
- The bundled scripts in this sub-skill are safe post-processing helpers. They
  consume JSON logits/labels and do not import TensorFlow or require original
  checkpoints.

## Two-Sentence Relation Models

The repo contains two main relation-input conventions. Pick the convention
before writing feeds, shape checks, or preprocessing code.

### Variant A: One Concatenated Sequence With `EOS`

Use this when the model exposes one `input_x` tensor shaped
`[batch, sequence_length]` and binary sparse labels shaped `[batch]`.

Expected preprocessing pattern:

1. Start from a pair record containing sentence-1 tokens, a tab separator,
   sentence-2 tokens, and a `__label__` suffix.
2. Replace the tab between the two sentences with the literal token `EOS`.
3. Map tokens to integer ids with a vocabulary that includes `EOS`.
4. Pad/truncate the single concatenated id list to `sequence_length`.
5. Feed `input_x`, `input_y`, and `dropout_keep_prob`.

The distilled architecture is embedding lookup, bidirectional LSTM, concatenate
forward/backward outputs, mean-pool across time, then a projection to
`[batch, num_classes]` logits. Training uses
`sparse_softmax_cross_entropy_with_logits` plus L2 regularization and an Adam
optimizer through TensorFlow 1.x helpers.

Operational notes:

- `EOS` is a semantic separator, not padding. If it is missing from the
  vocabulary, the relation model loses the boundary between questions.
- The labels in the original relation examples are usually binary: `0` means no
  relation, `1` means related.
- Use `dropout_keep_prob=1.0` for evaluation or exported-logit generation.

### Variant B: Two Separate CNN Inputs (`text1`, `text2`)

Use this when the model exposes two tensors:

- `input_x`: first sentence, `[batch, sequence_length]`;
- `input_x2`: second sentence, `[batch, sequence_length]`;
- `input_y`: sparse labels, `[batch]`.

Expected preprocessing pattern:

1. Parse exactly one tab-separated sentence pair before `__label__`.
2. Tokenize each side independently.
3. Pad each side to the same `sequence_length`.
4. Feed both tensors in the same example order.

The distilled architecture uses a shared embedding table, applies parallel
TextCNN filter/pool/dropout blocks to sentence 1 and sentence 2, concatenates
the two pooled vectors, and projects from
`num_filters * len(filter_sizes) * 2` to `num_classes`. Loss is sparse softmax
cross entropy for one relation label per pair.

Operational notes:

- Do not silently fall back to the `EOS` variant if a line cannot be split into
  two sides. Malformed relation TSV should be repaired or rejected before graph
  feeding.
- Keep the same token vocabulary for both sentence sides.
- Filter-size choices must be no larger than the padded sequence length.

## TextCNN + RCNN Hybrid Variant

The hybrid model is a single-sequence classifier whose final logits are a
learned weighted sum of a TextCNN branch and an RCNN-style recurrent-context
branch. It can be useful when a user asks about `TextCNN_with_RCNN` behavior or
how to port its shape/loss assumptions.

Shape summary:

- Input ids: `input_x` with shape `[batch, sequence_length]`.
- Embeddings: `[batch, sequence_length, embed_size]`.
- CNN branch: expand to `[batch, sequence_length, embed_size, 1]`, apply multiple
  `filter_size x embed_size` 2D convolutions, max-pool each filter output,
  concatenate to `[batch, num_filters_total]`, then project to
  `[batch, num_classes]`.
- RCNN branch: build left and right recurrent contexts, concatenate
  `[left_context, current_embedding, right_context]` at each position to form
  `[batch, sequence_length, embed_size * 3]`, reduce-max over time to
  `[batch, embed_size * 3]`, then project to `[batch, num_classes]`.
- Final logits: `sigmoid(weight1) * cnn_logits + (1 - sigmoid(weight1)) *
  rcnn_logits`.

Loss and feed notes:

- Single-label mode uses `input_y` and sparse softmax cross entropy.
- Multi-label mode uses `input_y_multilabel` shaped `[batch, num_classes]` and
  sigmoid cross entropy summed over classes. The graph-level accuracy in this
  mode is a placeholder constant, so compute real multi-label metrics outside
  the graph.
- The RCNN branch creates boundary variables shaped `[batch_size, embed_size]`.
  If recreating the graph, keep the runtime batch size consistent or refactor
  those tensors to dynamic batch shapes.

## Boosting Label Weights

The boosting helper pattern is label-centric reweighting based on validation
performance:

1. After an epoch, run validation data through the model and collect logits
   shaped `[num_examples, num_classes]` plus sparse true labels shaped
   `[num_examples]`.
2. Predict each example with `argmax(logits, axis=1)`.
3. Accumulate per-label `(count, correct)` statistics.
4. Convert each label's statistics to accuracy `correct / count`.
5. For a training batch, set each example's loss weight to
   `min(max_weight, 1.0 / (label_accuracy + epsilon))`; the original cap was
   `1.5` and epsilon was `0.001`.
6. Apply the weights to sparse softmax cross entropy, for example with
   TensorFlow 1.x `tf.losses.sparse_softmax_cross_entropy(labels, logits,
   weights=weights)`.

Use the bundled helper when you already have validation logits and labels:

```bash
python scripts/compute_boosting_label_weights.py \
  --logits-json '[[0.1, 0.9], [2.0, -1.0], [0.7, 0.2]]' \
  --labels-json '[1, 1, 0]' \
  --answer-list-json '[1, 0, 1]' \
  --max-weight 1.5
```

Interpretation:

- Low-accuracy labels get larger batch weights.
- The cap prevents extremely large losses when validation accuracy is near zero.
- Labels not observed in validation should be handled deliberately. The bundled
  script errors by default for missing batch labels unless a fallback accuracy
  is provided.

## Ensemble Logit Combination

The full source-style ensemble predictor builds multiple TensorFlow graphs,
restores several checkpoint directories, runs each model on the same examples,
then combines logits with a weighted sum before selecting top-k labels. A
representative weight pattern is two CNN-family models at `0.3` each plus two
memory-family models at `0.2` each. Memory-model internals are outside this
sub-skill; the ensemble contract here is about compatible logits.

Before combining logits, verify:

- every model uses the same label index to label string mapping;
- every model saw the same examples in the same order;
- every logits array has exactly the same `[num_examples, num_classes]` shape;
- weights are in the intended model order;
- full TensorFlow restoration has all required checkpoints, or else you are
  using exported logits instead of the source predictor.

Use the bundled helper for checkpoint-free post-processing:

```bash
python scripts/combine_logits_topk.py \
  --logits-json '[[[0.1, 0.9], [2.0, 1.0]], [[0.3, 0.4], [0.5, 2.5]]]' \
  --weights '0.6,0.4' \
  --label-map-json '{"0":"not_related","1":"related"}' \
  --top-k 1
```

The expected logits JSON shape is either:

- `[models][examples][classes]` for multiple models, or
- `[examples][classes]` for a single model.

The helper treats inputs as additive scores. If you pass probabilities instead
of raw logits, document that choice and keep all models calibrated the same way.
