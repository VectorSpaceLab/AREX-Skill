# Sequence and Memory Model Reference

This reference covers the repository's sequence-generation and memory-family models. It intentionally describes safe operating contracts rather than prescribing direct execution of the original long-running training scripts.

## Legacy runtime context

The model files are TensorFlow 1.x scripts. They use placeholders, sessions, `tf.app.flags`, `tf.contrib.layers.optimize_loss`, `tensorflow.contrib.rnn`, TFLearn `pad_sequences`, Python 2-era idioms such as `reload(sys)`/`sys.setdefaultencoding`, and local script imports. Plan with Python 3.7 and TensorFlow 1.x/TFLearn compatibility in mind. TensorFlow 2.x eager execution, `tf.keras` rewrites, and Python 3.13 assumptions are unsafe unless the future task explicitly asks for a port.

Full training/prediction is not immediately runnable from this skill. Expect external training files, pretrained word2vec binaries, cache directories, checkpoint directories, and substantial runtime. Use label formatting and graph-shape reasoning before attempting any native run.

## Model routing summary

| Need | Prefer | Why | Avoid when |
| --- | --- | --- | --- |
| Multi-label output as an ordered, fixed-length list of label ids | Seq2seq with attention or Transformer seq2seq | Decoder predicts one label token per time step and can stop with `_END` | Labels are naturally unordered and top-k sigmoid scores are sufficient |
| General attention architecture or toy sequence reversal/generation | Transformer seq2seq | Encoder-decoder stack with masked decoder self-attention and encoder-decoder attention | You only need single-label classification or do not have fixed decoder length |
| Single-label classification with Transformer features | Transformer classification variant | Uses encoder output flattened into one logits vector | You need multi-label sigmoid, decoder outputs, or BERT-style pretraining |
| Context/query/answer or QA-like setup | EntityNetwork or DMN | Inputs include `story`, `query`, and answer labels; memory state tracks facts | You only have one flat sentence and no meaningful query/context split |
| Multi-hop reasoning over facts | DMN | Repeated episodic memory passes can revisit relevant facts | Story length is one and no transitive inference is required |

## Seq2seq with attention

Evidence: README Seq2seq section; `a06_Seq2seqWithAttention/a1_seq2seq.py`; `a1_seq2seq_attention_model.py`; train/predict scripts; seq2seq branch in `data_util_zhihu.py`.

Architecture:

1. Word embedding for encoder input `input_x`.
2. Forward and backward custom GRU loops over `sequence_length` tokens.
3. Concatenated encoder states form attention states with shape `[batch, sequence_length, hidden_size * 2]`.
4. Decoder uses label embeddings and a custom GRU cell that also receives an attention context vector.
5. Projection produces logits for every decoder step.

Important placeholders and outputs:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `input_x` | `[batch, sequence_length]` (`None` batch in model, fixed slices in train code) | Tokenized source text padded to fixed length. |
| `decoder_input` | `[batch, decoder_sent_length]` | Shifted label sequence beginning with `_GO`. |
| `input_y_label` | `[batch, decoder_sent_length]` | Target label sequence ending with `_END` or truncating at fixed length. |
| `dropout_keep_prob` | scalar float | Dropout keep probability. |
| `logits` | `[batch_size, decoder_sent_length, num_classes]` | Per-step label-token logits. |
| `predictions` | `[batch_size, decoder_sent_length]` | `argmax` label-token ids per decoder step. |

The label vocabulary inserts `_GO`, `_END`, and `_PAD` before ordinary labels when `use_seq2seq=True`; `num_classes` must include those additional tokens. Training uses teacher forcing (`decoder_input` is the shifted gold label sequence). Prediction initializes decoder input with `_GO` and `_PAD` tokens, then filters duplicate labels, `_PAD`, and `_END` from per-step logits.

Use this framing when the order and maximum count of predicted labels matter enough to model them as a generated sequence. For ordinary multi-label classification, a sigmoid classifier may be simpler and less brittle.

## Transformer seq2seq

Evidence: README Transformer section; `a07_Transformer/a2_transformer.py`; encoder/decoder/attention building blocks; train/predict scripts; shared seq2seq data utility branch.

The full Transformer model mirrors encoder-decoder sequence generation:

- Encoder input placeholder: `input_x` with shape `[batch_size, sequence_length]`.
- Decoder input placeholder: `decoder_input` with shape `[batch_size, decoder_sent_length]`.
- Target placeholder: `input_y_label` with shape `[batch_size, decoder_sent_length]`.
- Output: `logits` with shape `[batch_size, decoder_sent_length, num_classes]`.

Key components:

- Token embeddings are multiplied by `sqrt(d_model)` and combined with learned positional masks.
- `Encoder` applies multi-head self-attention and position-wise feed-forward blocks.
- `Decoder` applies masked decoder self-attention, encoder-decoder attention, and position-wise feed-forward blocks.
- The decoder mask is a lower-triangular attention mask (`-1e9` above the diagonal) so a position should not attend to future labels.
- Defaults in scripts often use `d_model=512`, `d_k=64`, `d_v=64`, `h=8`, and `num_layer=1` even though the paper describes 6 layers.

The seq2seq Transformer has fixed `batch_size` placeholders. Any input array whose first dimension differs from the configured batch size will fail graph execution. Prediction code creates a full `[batch_size, decoder_sent_length]` decoder-input matrix, puts `_GO` in the first column, and fills the rest with `_PAD`.

## Transformer classification variant

Evidence: README notes that classification uses only the encoder; `a07_Transformer/a2_transformer_classification.py`; train/predict classification scripts.

This is a separate class with the same class name (`Transformer`) but a different contract from seq2seq:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `input_x` | `[batch_size, sequence_length]` | Padded token ids. |
| `input_y_label` | `[batch_size]` | Single class id. |
| `logits` | `[batch_size, num_classes]` | Single-label logits. |
| `predictions` | `[batch_size]` | Argmax class id. |

The classification variant uses only the encoder, reshapes encoded states to `[batch_size, sequence_length * d_model]`, and applies one projection. It does not use `decoder_input`, `_GO`, `_END`, or `_PAD` label tokens. The source comments state that the classification adaptation removed the decoder, uses no causal mask, often uses one layer, and can optionally control residual connections.

Route to this variant only when the task is single-label classification or a top-k ranking over one logits vector. It is not a drop-in replacement for multi-label sigmoid training without code changes.

## Recurrent Entity Network

Evidence: README Recurrent Entity Network section; `a08_EntityNetwork/a3_entity_network.py`; train/predict scripts; data utility copy.

The EntityNetwork models context and query jointly. The source training scripts adapt ordinary text classification by using the same padded sentence both as query and as a one-sentence story (`np.expand_dims(trainX, axis=1)`), but the model's native abstraction is QA-like.

Core placeholders:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `story` | `[batch, story_length, sequence_length]` | Context/fact sentences as token ids. |
| `query` | `[batch, sequence_length]` | Question or text to classify. |
| `answer_single` | `[batch]` | Single-label target for softmax loss. |
| `answer_multilabel` | `[batch, num_classes]` | Multi-label multi-hot target for sigmoid loss. |
| `logits` | `[batch, num_classes]` | Answer/class logits. |

Memory mechanics:

- The input encoder is either bag-of-words with learned position masks or an optional bidirectional LSTM encoder.
- Memory has `block_size` independent key/value blocks. Defaults in the training script use `block_size=20` and `story_length=1` for classification adaptation.
- For each story sentence, the cell computes a gate from similarity between the input, hidden value block, and key block; computes a candidate hidden state; updates each block; and L2-normalizes hidden states.
- The output module attends from the query vector over hidden state blocks, sums the memory, applies a nonlinearity, and projects to labels.

Use EntityNetwork when the task can be expressed as facts/context plus a query and answer. For plain text classification, the repo uses it as an experimental memory classifier; check whether a flat classifier is simpler before adopting it.

## Dynamic Memory Network

Evidence: README Dynamic Memory Network section; `a09_DynamicMemoryNet/a8_dynamic_memory_network.py`; train/predict scripts.

The DMN separates input, question, episodic memory, and answer modules.

Core placeholders:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `story` | `[batch, story_length, sequence_length]` | Context/facts as token ids. |
| `query` | `[batch, sequence_length]` | Question/text. |
| `answer_single` | `[batch]` | Single-label answer. |
| `answer_multilabel` | `[batch, num_classes]` | Multi-label answer. |
| `logits` | `[batch, num_classes]` or `[batch, sequence_length, num_classes]` | Depends on `decode_with_sequences`. |

Mechanics and important flags:

- `input_module` embeds each story sentence and runs a GRU over the story dimension, producing `[batch, story_length, hidden_size]` fact representations.
- `question_module` embeds the query and runs a GRU to produce `[batch, hidden_size]`.
- `episodic_memory_module` repeats for `num_pass` passes. Each pass computes gate scores from candidate facts, previous memory, and question; then either uses `gated_gru` over facts or a weighted sum of facts.
- `num_pass` controls memory hops; the training script defaults to `2`.
- `use_gated_gru` chooses the memory update mechanism. The README emphasizes gated-GRU updates, while the provided training script sets the flag default to `False` for one experiment.
- `decode_with_sequences=False` returns one answer logits vector for classification. If `True`, the answer module loops for `sequence_length` steps and returns sequence logits; that path needs careful target-shape design.

Use DMN for multi-hop QA-like contexts or when a memory pass over facts is central. If `story_length=1` and the story is just the same text as the query, the model is being used as an experimental classifier rather than as a full DMN reasoning setup.

## Safe adaptation pattern

Before any model run:

1. Validate raw lines and label maps with the data-preparation sub-skill.
2. For seq2seq, generate a tiny decoder-input/target example using the bundled formatter and compare it against the intended label map.
3. Confirm `num_classes`: ordinary labels only for EntityNetwork/DMN/Transformer classifier; ordinary labels plus `_GO`, `_END`, `_PAD` for seq2seq models.
4. Confirm fixed dimensions: `batch_size`, `sequence_length`, `decoder_sent_length`, `story_length`, `block_size`, `num_pass`, `d_model`, and embedding dimension must match arrays and checkpoint variables.
5. Confirm external artifacts: word2vec binary, training data, checkpoint directory, label vocabulary cache, and any expected pickle/HDF5 cache are available.
6. Only then decide whether to run graph construction, a tiny synthetic batch, or a full training/prediction workflow.
