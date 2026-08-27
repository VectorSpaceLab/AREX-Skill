# Seq2seq Label Workflows

The repository uses seq2seq models to cast multi-label classification as label-token generation. A text encoder consumes input words, while a decoder generates a fixed-length label sequence. The label vocabulary is distinct from the word vocabulary.

## Special label tokens

When the shared data utility is called with `use_seq2seq=True`, it prepends three special tokens to the label vocabulary:

| Token | Typical index in source utilities | Role |
| --- | --- | --- |
| `_GO` | `0` | First decoder input token during training and prediction. |
| `_END` | `1` | Target token that marks the logical end of generated labels. |
| `_PAD` | `2` | Padding token for unused decoder positions. |

Do not use a word-vocabulary padding id as a label padding id. Seq2seq label embeddings use the label vocabulary, not the word vocabulary.

## Decoder input and target shift

For a fixed `decoder_sent_length`, the model needs two aligned arrays:

- `decoder_input`: the teacher-forcing input to the decoder. It begins with `_GO`, then gold labels, then `_PAD`.
- `input_y_label` / target: the token each decoder step should predict. It begins with the first gold label, ends with `_END` if space remains, then `_PAD`.

Example with decoder length 6:

| Raw labels | Decoder input | Target labels |
| --- | --- | --- |
| `L1` | `[_GO, L1, _PAD, _PAD, _PAD, _PAD]` | `[L1, _END, _PAD, _PAD, _PAD, _PAD]` |
| `L1 L2 L3` | `[_GO, L1, L2, L3, _PAD, _PAD]` | `[L1, L2, L3, _END, _PAD, _PAD]` |
| `L1 L2 L3 L4 L5` | `[_GO, L1, L2, L3, L4, L5]` | `[L1, L2, L3, L4, L5, _END]` |
| `L1 L2 L3 L4 L5 L6 L7` | `[_GO, L1, L2, L3, L4, L5]` | `[L1, L2, L3, L4, L5, _END]` |

The bundled formatter follows the source utility's effective fixed-length behavior: at most `decoder_length - 1` ordinary labels are retained, and the last target position is `_END` when the raw label list is longer than that capacity. This means there is no target slot for a sixth ordinary label when `decoder_length=6`; the final target slot is reserved for `_END`.

Use the helper:

```bash
python sub-skills/sequence-and-memory-models/scripts/format_seq2seq_labels.py \
  --decoder-length 6 L1 L2 L3
```

The JSON output contains `decoder_input`, `target`, and metadata showing whether labels were truncated.

## Numeric label ids versus strings

The source training code ultimately feeds integer ids from `vocabulary_word2index_label`. The formatter emits token strings by default because this is safer for reviewing label logic. If a future task needs numeric ids, first build or load the exact label vocabulary used by the model checkpoint, then map each token string to its id consistently.

For seq2seq models:

- `num_classes` must equal the number of ordinary label ids plus the special label tokens.
- `Embedding_label` must be sized with that `num_classes`.
- The checkpoint, label vocabulary cache, and runtime `num_classes` must agree.

For non-seq2seq models in this sub-skill, do not add `_GO`, `_END`, and `_PAD` unless the source code explicitly expects them. EntityNetwork, DMN, and Transformer classification normally use ordinary label outputs.

## Prediction-time decoding

The prediction scripts initialize decoder input with `_GO` and `_PAD` values. The Seq2seqWithAttention predictor uses a one-row decoder input, while Transformer seq2seq prediction builds a full `[batch_size, decoder_sent_length]` matrix.

The source prediction helpers inspect per-step logits and choose high-scoring labels while filtering:

- already emitted labels,
- `_PAD`,
- `_END`,
- often the last decoder column because it is expected to be the end token.

This filtering is a heuristic over logits, not a guarantee of calibrated multi-label probabilities. If combining outputs with a flat classifier, route the combination logic to `relation-and-ensemble-workflows` and ensure both models use the same label map.

## When to use seq2seq labels for classification

Use this framing when:

- the task has a bounded number of labels per example,
- label order is meaningful or an ordered decoding heuristic is acceptable,
- a decoder can model dependencies between selected labels,
- fixed decoder length and truncation are acceptable.

Prefer a flat sigmoid multi-label classifier when:

- labels are unordered,
- the number of possible labels is large and output count varies widely,
- you need independent calibrated probabilities,
- you cannot afford decoder training or do not have checkpoint/data artifacts.

## Common checks

Before feeding arrays into a seq2seq model, assert:

1. Every `decoder_input` row and every target row has exactly `decoder_sent_length` elements.
2. `decoder_input[:, 0]` is `_GO`.
3. Target rows include `_END` at the first unused label position, or in the last target position when raw labels overflow capacity.
4. Remaining unused positions are `_PAD`.
5. No ordinary label id collides with `_GO`, `_END`, or `_PAD`.
6. `decoder_input` and `target` use label-vocabulary ids, not word-vocabulary ids.
