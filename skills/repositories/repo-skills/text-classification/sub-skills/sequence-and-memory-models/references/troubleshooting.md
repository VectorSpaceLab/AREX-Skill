# Troubleshooting Sequence and Memory Models

Use this page before planning any TensorFlow execution. Most failures in this part of the repository are environment, artifact, shape, or label-shift issues rather than architecture mistakes.

## TensorFlow and Python compatibility

Symptoms:

- `ModuleNotFoundError: No module named 'tensorflow.contrib'`
- `AttributeError: module 'tensorflow' has no attribute 'placeholder'`
- `tf.app.flags` or `tf.Session` errors
- `NameError: name 'reload' is not defined` or `sys.setdefaultencoding` issues

Likely cause:

- Running legacy TensorFlow 1.x code under TensorFlow 2.x, modern Keras-only APIs, or an incompatible Python version.

Action:

- Use a Python 3.7-era TensorFlow 1.x/TFLearn environment for inspection and graph work.
- Do not assume Python 3.13 or TensorFlow 2.x eager execution can run these files unchanged.
- If porting is required, treat it as a separate modernization task, not as normal operation of this repo skill.

## Missing external artifacts

Symptoms:

- Word2vec binary not found.
- Label or vocabulary pickle cache not found.
- Checkpoint directory has no `checkpoint` file.
- Training file names such as Zhihu title/description datasets are missing.
- Full prediction script exits after printing that no checkpoint exists.

Likely cause:

- The repository does not bundle all large training data, pretrained embeddings, generated caches, or trained checkpoints needed for full training/prediction.

Action:

- Do not claim the original training/prediction scripts are immediately runnable.
- First run safe formatting and data validation helpers.
- Ask the user to provide the exact data, embedding, cache, and checkpoint artifacts if full reproduction is required.
- Check that checkpoint hyperparameters (`num_classes`, dimensions, sequence lengths, label vocabulary) match the model instance.

## Seq2seq decoder off-by-one errors

Symptoms:

- Target arrays are shifted by one position.
- Model learns to predict `_GO` as an output label.
- `_END` never appears, appears too early, or overwrites a real label unexpectedly.
- Loss shape is `[batch, decoder_length]` but labels have another length.

Likely cause:

- Confusing `decoder_input` with `input_y_label`, using word-vocabulary ids for labels, or forgetting that the last target slot is reserved for `_END` under fixed length.

Action:

- Generate a tiny example with `scripts/format_seq2seq_labels.py`.
- Verify `decoder_input = [_GO] + labels[:decoder_length-1] + pads`.
- Verify `target = labels[:decoder_length-1] + [_END] + pads`, trimmed to fixed length.
- Confirm special tokens are in the label vocabulary and counted in `num_classes`.

## Fixed batch-size placeholders

Symptoms:

- TensorFlow feed error: cannot feed value of shape `(n, ...)` for tensor shaped `(batch_size, ...)`.
- Last prediction batch is skipped or mismatched.
- Transformer seq2seq/classification works with one batch but fails with another.

Likely cause:

- Transformer and memory model classes often define placeholders with a fixed `batch_size`, not `None`. The original scripts iterate in full batches and may drop remainders.

Action:

- Pad or batch inputs so every fed batch has exactly the configured `batch_size`.
- For safe graph checks, choose `batch_size=1` or a tiny fixed batch and keep arrays aligned.
- If adapting for production, add explicit remainder handling or rebuild the graph with dynamic batch dimensions.

## Sequence length and decoder length mismatches

Symptoms:

- Embedding lookup succeeds but reshape or projection fails.
- Transformer classification projection has unexpected dimensions.
- Decoder logits shape does not match target labels.

Likely cause:

- `sequence_length`, `decoder_sent_length`, and projection matrices are fixed at graph construction. Transformer classification projects from `sequence_length * d_model`; seq2seq models project per decoder step.

Action:

- Record and keep constant: `sequence_length`, `decoder_sent_length`, `d_model`, `hidden_size`, and `num_classes`.
- Pad text to exactly `sequence_length` before feed.
- Pad/truncate label sequences to exactly `decoder_sent_length` before feed.
- Do not restore a checkpoint into a graph with different dimensions.

## EntityNetwork and DMN story/query shape errors

Symptoms:

- A feed with shape `[batch, sequence_length]` fails for `story`.
- Memory model behaves like a flat classifier and ignores intended context.
- Shape errors mention rank 3, `story_length`, or `sequence_length`.

Likely cause:

- EntityNetwork and DMN require both `story=[batch, story_length, sequence_length]` and `query=[batch, sequence_length]`. The source classification adaptation uses `np.expand_dims(text_batch, axis=1)` to create a one-sentence story, but QA-like tasks need real multi-sentence stories.

Action:

- For classification adaptation, feed `story = expand_dims(query_tokens, axis=1)` only when `story_length=1` is intentional.
- For QA-like tasks, build a real 3-D story tensor with exactly `story_length` fact rows per example.
- Keep query separate from story; do not feed the same 2-D array into both placeholders.

## Memory hyperparameter pitfalls

Symptoms:

- EntityNetwork memory states have unexpected dimensions.
- DMN output shape is a sequence instead of one answer vector.
- Training is very slow or unstable.

Likely cause:

- Misunderstanding `block_size`, `num_pass`, `use_gated_gru`, or `decode_with_sequences`.

Action:

- EntityNetwork: `block_size` is the number of independent memory blocks; output attention attends over those blocks.
- DMN: `num_pass` is the number of episodic memory hops; more passes increase work and may change behavior.
- DMN: `use_gated_gru=True` uses gated GRU memory updates; `False` uses weighted-sum episode construction.
- DMN: keep `decode_with_sequences=False` for single/multi-label classification. If set to `True`, design sequence targets deliberately.

## Multi-label versus single-label loss mismatch

Symptoms:

- Accuracy is a constant `0.5`.
- Labels have shape `[batch, num_classes]` but softmax loss expects `[batch]`.
- Predictions are a single argmax despite multi-label targets.

Likely cause:

- In EntityNetwork/DMN multi-label mode, the source uses sigmoid cross entropy over multi-hot targets and leaves graph accuracy as a placeholder constant. In single-label mode, it uses sparse softmax.

Action:

- Multi-label: feed `answer_multilabel` with shape `[batch, num_classes]` and compute evaluation outside the graph.
- Single-label: feed `answer_single` with shape `[batch]`.
- Do not interpret the constant graph accuracy as a real metric in multi-label mode.

## Prediction filtering and duplicate labels

Symptoms:

- Seq2seq prediction contains repeated labels or special tokens.
- The last decoder step always looks like `_END` or is ignored.

Likely cause:

- The source prediction helper ranks logits per decoder row and manually filters duplicates, `_PAD`, and `_END`. It does not perform a fully autoregressive beam search.

Action:

- Filter special tokens and duplicates before writing predictions.
- Keep label-map consistency if combining with logits from another model.
- For calibrated probabilities, prefer a flat sigmoid classifier or design a custom decoding/evaluation layer.

## Safer first checks

Before any full run:

1. Run `python sub-skills/sequence-and-memory-models/scripts/format_seq2seq_labels.py --help`.
2. Run one tiny formatting example and inspect JSON.
3. Validate raw data and label maps via the data-preparation sub-skill.
4. If TensorFlow is available, build a tiny graph only after dimensions and imports are fixed.
5. Start full training/prediction only after the user supplies required external artifacts and accepts runtime cost.
