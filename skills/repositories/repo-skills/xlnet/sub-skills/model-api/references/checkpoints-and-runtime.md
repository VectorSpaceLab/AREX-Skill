# Checkpoints and Runtime

## What a released XLNet bundle contains

The release zip ships three files that work together:

- `xlnet_config.json` — model hyperparameters.
- `spiece.model` — SentencePiece tokenizer model.
- `xlnet_model.ckpt` — TensorFlow checkpoint prefix plus its shard files.

Keep the roles separate:

- `model_config_path` points to the JSON.
- `spiece_model_file` points to the SentencePiece model.
- `init_checkpoint` points to the checkpoint prefix, not the output folder.
- `model_dir` is the run workspace for new checkpoints and event files.

## Direct build order

1. Validate the config JSON with `scripts/inspect_xlnet_config.py`.
2. Create `XLNetConfig` and `RunConfig`.
3. Build `XLNetModel` with `[len, bsz]` tensors.
4. Pick `get_pooled_out()` for one-vector heads or `get_sequence_output()` for token-level heads.
5. Add the task head with `get_initializer()`.
6. Load weights with `model_utils.init_from_checkpoint()`.
7. Build the optimizer with `model_utils.get_train_op()`.

## Output choice guide

| Need | Best choice | Why |
| --- | --- | --- |
| One prediction per example | `get_pooled_out()` | Returns `[bsz, d_model]`, which matches classifiers and regressors. |
| Token/span answers | `get_sequence_output()` | Preserves the full `[len, bsz, d_model]` sequence. |
| Streaming or chunked inference | `get_new_memory()` | Lets the next chunk reuse cached states from the previous chunk. |
| Tied LM projection | `get_embedding_table()` | Reuse the base embedding matrix for output projection. |
| Learned sequence summary | `get_pooled_out(summary_type='attn')` or `modeling.summarize_sequence(..., summary_type='attn')` | Learns a mask-aware summary instead of picking a single token. |

### Custom classifier decision rule

- If the label is sequence-level, start with `get_pooled_out('last')`.
- If padding makes the final token unreliable, prefer `summary_type='mean'` or `summary_type='attn'`.
- If the label depends on a token span or any token can matter, use `get_sequence_output()`.

## Checkpoint helpers and caveats

| Helper | Best use | Caveat |
| --- | --- | --- |
| `model_utils.init_from_checkpoint()` | Map a pretrained checkpoint into the current graph. | It matches by variable name. A config mismatch, such as a missing `untie_r` key, will usually break before or during restore. |
| `model_utils.clean_ckpt()` | Publish or reuse a checkpoint without optimizer baggage. | It removes `global_step` and Adam-slot variables, so it is not a full training-state snapshot. |
| `model_utils.avg_checkpoints()` | Average the last few training checkpoints before evaluation or a new warm start. | It averages variable tensors only; it does not preserve optimizer slots or exact step state. Use only when the averaged checkpoints share the same architecture and variable names. |
| `gpu_utils.load_from_checkpoint()` | Restore the latest checkpoint from a logdir into the current session. | It requires a live `tf.Session` and a `tf.train.Saver`. |

## Runtime and optimizer notes

- `model_utils.configure_tpu()` is legacy TensorFlow 1.x graph code. It returns a `tf.contrib.tpu.RunConfig` and only works in the TF1 contrib runtime.
- On non-TPU multi-GPU setups, `configure_tpu()` switches to `MirroredStrategy` when `num_core_per_host > 1`.
- `model_utils.get_train_op()` builds warmup plus polynomial or cosine decay. It also applies optional layerwise gradient decay when `FLAGS.lr_layer_decay_rate != 1.0`.
- `weight_decay > 0` is rejected for multi-GPU non-TPU training by the helper. Keep that path single-device or TPU-backed, or implement your own optimizer flow.
- `gpu_utils.assign_to_gpu()` and `gpu_utils.average_grads_and_vars()` are only needed for manually assembled towers. If the task wrapper already handles the topology, you usually do not need them.

## SentencePiece and text normalization

- `prepro_utils.preprocess_text()` should usually run before `encode_pieces()` or `encode_ids()`.
- `encode_pieces()` preserves the repo's special handling for comma-after-digit pieces; do not remove that logic if you need tokenization parity.
- `sample=True` activates stochastic SentencePiece sampling and is not the default path for deterministic inference or preprocessing.

## Practical checkpoint path mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Pointing `model_dir` at the pretrained bundle | New training writes into the wrong place or reuses the source checkpoint location. | Keep `model_dir` separate from `init_checkpoint`. |
| Pointing `init_checkpoint` at a directory when a prefix is expected | Restore fails or resolves the wrong checkpoint. | Pass the checkpoint prefix, or use the helper's `latest` suffix convention when you want the newest file in a checkpoint directory. |
| Reusing a checkpoint built with a different config | Variable restore or shape mismatch errors. | Make the JSON, checkpoint, and head architecture agree before building the graph. |
