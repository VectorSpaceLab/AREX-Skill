# Classification Model Reference

This reference distills the repository's classic classification models into operational guidance. It is intentionally TensorFlow 1.x oriented: placeholders, static graphs, `tf.Session`, `tf.contrib`, and TFLearn examples are expected. TensorFlow 2.x compatibility is not implied.

## Model selection

| Need | Prefer | Why | Avoid when |
| --- | --- | --- | --- |
| Fast multi-label baseline over token ids and optional n-grams | fastTextB | Embedding lookup, average pooling over tokens, linear label projection, sigmoid multi-label loss. Fastest path for sanity checks. | Word order and phrase position are central beyond n-gram preprocessing. |
| Strong classic multi-label sentence baseline | TextCNN | Parallel filters over embeddings, global max-pooling, dropout, dense projection, sigmoid loss. README reports it as a strong baseline among classic models. | Very long documents need hierarchical structure, or TensorFlow 1.x batch-norm/update-op behavior cannot be controlled. |
| Single-label sequence order baseline | TextRNN | Bidirectional LSTM over token ids with last-step or stacked recurrent output and sparse-softmax loss. | Need current multi-label support without editing; the common model is single-label. |
| Context-sensitive word representation with max-pooling | TextRCNN | Left-context, current-word, and right-context representation per token, max-pooling, single/multi-label loss variants. | Variable runtime batch sizes are required; some variants bake `batch_size` into context variables. |
| Document or title+description split into sections | Hierarchical Attention Network | Word-level encoder/attention followed by sentence-level encoder/attention and classifier. | Input length is not divisible by `num_sentences`, or the training script imports an unintended variant. |
| Contextual encoder and BERT-style classification head | BERT | `BertModel` pooled `[CLS]` output plus sigmoid multi-label or softmax single-label head, masks, and segment ids. | No compatible BERT vocab/config/checkpoint exists, or memory budget is small. |
| Legacy educational examples | TFLearn | Small fully connected or CNN examples showing old TFLearn data-flow patterns. | Production text classification; these examples download/use toy datasets and do not represent the main Zhihu workflow. |

## fastTextB multi-label model

The fastTextB multi-label model is the repository's simplest classic classifier:

1. `sentence`: integer token ids with shape `[None, sentence_len]`.
2. `Embedding`: trainable lookup table `[vocab_size, embed_size]`.
3. Token embeddings are averaged across the sentence axis to create `[None, embed_size]`.
4. `W` and `b` project to logits `[None, label_size]`.
5. Active loss is sigmoid cross entropy against `labels_l1999` multi-hot targets `[None, label_size]`, summed per example and averaged, plus L2 regularization.

The source comments discuss NCE/hierarchical-softmax-style alternatives, but the active multi-label path uses sigmoid cross entropy over the dense multi-hot label matrix. Keep `labels` with shape `[None, max_label_per_example]` only if you are reviving the inactive sampled-loss path.

Best use: a quick multi-label baseline when token order is secondary and preprocessing can add unigram/bigram/trigram ids.

## TextCNN model

The main TextCNN model accepts token ids `input_x` with shape `[None, sequence_length]` and multi-hot labels `input_y_multilabel` with shape `[None, num_classes]`.

Core graph:

1. `Embedding`: `[vocab_size, embed_size]`.
2. Embedded words: `[batch, sequence_length, embed_size]`.
3. Expanded channel axis: `[batch, sequence_length, embed_size, 1]`.
4. For each filter size, a 2-D convolution uses filter shape `[filter_size, embed_size, 1, num_filters]` with `VALID` padding.
5. Batch norm, ReLU, and max-pooling reduce each filter branch to `[batch, 1, 1, num_filters]`.
6. Branches concatenate into `h_pool` and flatten to `[batch, num_filters * len(filter_sizes)]`.
7. Dropout, a tanh dense layer, and final projection produce logits `[batch, num_classes]`.
8. In multi-label mode, sigmoid cross entropy is reduced by summing class losses per example and averaging across the batch.

The training script uses filter sizes `[6, 7, 8]`, `num_filters=128`, `embed_size=128`, `batch_size=64`, `dropout_keep_prob=0.8` for training, and `is_training_flag` to control batch normalization update behavior. Prefer `multi_label_flag=True`; the single-label branch in the current model is partly stale because its `input_y` placeholder is commented out.

## TextRNN models

The primary TextRNN is a single-label BiLSTM classifier:

- `input_x`: `[None, sequence_length]` token ids.
- `input_y`: `[None]` sparse integer class ids.
- Embeddings feed a forward and backward `BasicLSTMCell`.
- The forward/backward outputs concatenate to `[batch, sequence_length, hidden_size * 2]`.
- The common variant takes the last time step and projects it to logits `[batch, num_classes]`.
- Loss is `sparse_softmax_cross_entropy_with_logits` plus L2.

A multi-layer variant adds a second LSTM over the concatenated BiLSTM output and projects the final state. Treat both as single-label unless you deliberately add a multi-label label placeholder and sigmoid loss.

Important inspection warning: some TextRNN model files invoke their `test()` function at import time. Do not import them during broad automated inspection unless you first guard or sandbox that side effect.

## TextRCNN models

TextRCNN represents each token as a concatenation of left context, current embedding, and right context:

- `input_x`: `[None, sequence_length]` token ids.
- `Embedding`: `[vocab_size, embed_size]`.
- For each token, left and right context vectors are computed recurrently with learned matrices.
- Per-token representation is `[left_context, current_embedding, right_context]`, so the feature width is `embed_size * 3`.
- Max-pooling over the sequence yields `[batch, embed_size * 3]`.
- Dropout and projection produce logits `[batch, num_classes]`.

The RCNN variants include single-label sparse-softmax and multi-label sigmoid losses. The `mode2` variant uses ReLU in context updates and passes `batch_size` late in the constructor; other variants put `batch_size` earlier. Always inspect the actual constructor before adapting training or prediction code.

Caution: several RCNN variables and zero tensors are created with a fixed `batch_size`. Use consistent batch sizes during training, evaluation, and prediction, or refactor those tensors before dynamic batching.

## Hierarchical Attention Network

The classic HAN path models a flattened document that is split into `num_sentences` pieces:

- User-facing input is `input_x` with shape `[None, total_sequence_length]`.
- The model sets per-sentence length to `total_sequence_length / num_sentences` and reshapes to `[batch, num_sentences, sentence_length]`.
- Word-level GRU/BiLSTM encoders create hidden states per sentence.
- Word-level attention creates sentence representations.
- Sentence-level encoders and attention create a document representation.
- A dropout and projection layer produce logits.

The p1 HAN variant supports single-label sparse-softmax and multi-label sigmoid losses. A separate `HAN_model` variant is multi-task: it has separate logits and sigmoid losses for accusation, article, death penalty, and life imprisonment plus a regression-style imprisonment output. Use the multi-task variant only when the downstream labels match that multi-head contract.

Training-script caveat: one training script imports the classic HAN model and then imports a transformer-named HAN model into the same symbol. Confirm which class is active before claiming a specific architecture.

## BERT classification heads

The repository includes a Google-BERT-style TensorFlow 1.x `BertConfig` and `BertModel` implementation. BERT classification uses three input matrices:

- `input_ids`: `[batch, max_seq_length]` token ids, usually with a `[CLS]` id inserted at the front.
- `input_mask`: `[batch, max_seq_length]`, 1 for real tokens and 0 after padding.
- `segment_ids`: `[batch, max_seq_length]`, indicating sequence A/B segments.

The multi-label training path builds a `BertConfig`, obtains `model.get_pooled_output()`, and applies a dense classification head:

1. `output_weights`: `[num_labels, hidden_size]`.
2. `logits = pooled_output @ output_weights^T + output_bias` gives `[batch, num_labels]`.
3. `probabilities = sigmoid(logits)` for independent labels.
4. Loss is sigmoid cross entropy, summed over labels and averaged over examples.

The online prediction runner is a single-label/sequence-pair softmax pattern. It demonstrates tokenization, `[CLS]`/`[SEP]`, masks, and segment ids, but it should not be treated as the same contract as the multi-label BERT head without modification.

## TFLearn examples

The TFLearn examples are legacy educational patterns:

- A fully connected classifier over `[None, 784]` toy vectors with dropout and categorical cross entropy.
- A text CNN over IMDB ids: embedding, parallel `conv_1d`, global max-pooling, dropout, softmax.
- A CIFAR-10 image CNN example, useful only as TFLearn syntax evidence.

They require a TensorFlow/TFLearn stack compatible with the era of the examples. They may download or expect dataset caches and should not be used as proof that the main repository models train successfully.

## Safe graph-inspection strategy

Prefer graph-construction checks before running any training loop:

1. Start in a Python 3.7 / TensorFlow 1.x environment.
2. Use tiny vocab, label, sequence, filter, and hidden sizes.
3. Import only the needed model module from its own model directory.
4. Build the graph and inspect placeholder/logit/loss tensor shapes.
5. Do not initialize sessions, restore checkpoints, download datasets, or run training by default.

Use `scripts/inspect_tf1_model_shapes.py` for fastTextB, TextCNN, and BERT-config smoke inspection. TextRNN, RCNN, and HAN need more care because some files have import-time side effects, fixed-batch assumptions, or variant-shadowing traps.
