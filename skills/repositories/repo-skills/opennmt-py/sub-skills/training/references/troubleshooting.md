# Training troubleshooting

Use this reference after `scripts/inspect_train_config.py` or `onmt_train` reports a failure.

## Config does not parse or required fields are missing

Symptoms:

- YAML parse error.
- Missing `data`, `src_vocab`, `tgt_vocab`, `save_model`, `train_steps`, or `valid_steps`.
- Training starts with defaults you did not intend.

Actions:

1. Validate the YAML syntax with a YAML parser or the bundled inspector.
2. Keep training configs explicit even when OpenNMT-py has defaults.
3. For seq2seq, define `data` as a mapping with at least one training corpus and a `valid` corpus; each seq2seq corpus needs `path_src` and `path_tgt`.
4. For language modeling, set `model_task: lm`, `share_vocab: true`, and a source/shared vocab.
5. If vocab files are missing or stale, route to `../data-preparation/` and rebuild them before training.

## Data and vocabulary validation failures

Symptoms:

- `Please check path of your ... file!`
- `Corpus ... src/txt path is required`
- `tgt path is also required for non language modeling tasks`
- `vocab must be shared for LM task`
- `inferfeats transform is required when setting source features`

Actions:

1. Confirm every corpus path is reachable from the working directory where `onmt_train` is launched.
2. Confirm `src_vocab` exists and `tgt_vocab` exists unless `share_vocab: true` is intentional.
3. For `model_task: lm`, remove separate target vocab assumptions and keep `share_vocab: true`.
4. For source features, make sure the data contains feature separators and `inferfeats` is in the transform pipeline.
5. If data transforms changed after a checkpoint was created, expect a warning and prepare to rebuild vocab/transforms.

## Multi-GPU launch hangs or starts the wrong number of workers

Symptoms:

- Training hangs at startup.
- Only CPU training starts even though GPUs exist.
- Distributed process errors mention rank, NCCL, master address, or timeout.

Actions:

1. Check `CUDA_VISIBLE_DEVICES` before launching.
2. For one visible GPU, use `world_size: 1` and `gpu_ranks: [0]`.
3. For N visible GPUs on one node, use `world_size: N` and `gpu_ranks: [0, ..., N-1]`.
4. Do not set `world_size` smaller than the number of local `gpu_ranks`.
5. If `world_size == len(gpu_ranks)`, make sure rank `0` is included.
6. For multi-node rank slicing, make sure every node uses the same `world_size`, `master_ip`, and `master_port`, and uses a distinct local rank slice. Treat multi-node as advanced and validate with a tiny run first.
7. Increase `timeout` only after rank layout and networking are correct.

## Checkpoint continuation resumes the wrong behavior

Symptoms:

- Learning rate, optimizer, or step counter does not match expectations.
- New model options are ignored when training from a checkpoint.
- `update_vocab` fails validation.

Actions:

1. Decide which checkpoint mode is intended:
   - exact resume: `train_from` with `reset_optim: none`;
   - reuse weights with fresh optimizer: `reset_optim: all`;
   - update vocab: `update_vocab: true` with `reset_optim: states` or `all`;
   - advanced optimizer-state reuse with changed options: `keep_states`.
2. Remember that without `override_opts: true`, checkpoint model options dominate most current YAML model options.
3. If you set `override_opts: true`, restate the complete architecture and model task, not only the option you want to change.
4. For vocabulary update, rebuild vocab files first and keep `train_from` present.

## Pretrained embedding errors

Symptoms:

- `You need to specify an -embedding_type!`
- `-save_data should be set if use pretrained embeddings`
- Embedding tensor size mismatch or unexpected truncation/padding.

Actions:

1. Use raw embeddings through `both_embeddings`, `src_embeddings`, or `tgt_embeddings` only with `embeddings_type` and `save_data`.
2. Do not set `both_embeddings` together with side-specific embeddings.
3. Match `word_vec_size`, or side-specific vector sizes, to the embedding dimension.
4. Use `freeze_word_vecs_enc` and `freeze_word_vecs_dec` only when freezing loaded vectors is intended.
5. For torch-serialized vectors, set `pre_word_vecs_enc` and/or `pre_word_vecs_dec` directly.

## Alignment training fails

Symptoms:

- `alignment file path are required when lambda_align > 0.0`
- `Only transformer is supported to joint learn alignment`
- `alignment_layer should be smaller than number of layers`
- Poor or impossible alignments after tokenization.

Actions:

1. Set `decoder_type: transformer`.
2. Provide `path_align` for every training and validation corpus when `lambda_align > 0.0`.
3. Keep `alignment_layer` within the decoder layer range.
4. Avoid tokenization and token insertion/deletion transforms that change alignment indices.
5. Check alignment files for blank lines and make sure Pharaoh-style indices match the tokenized data used for training.
6. Use `alignment_heads: 1` for supervised head training unless a deliberate average-head setup is being tested.

## LoRA or quantized fine-tuning fails

Symptoms:

- Import error for bitsandbytes or AutoAWQ.
- `Cannot use LoRa with Enc/Dec-oder freezing`.
- LoRA options appear to have no effect.
- Quantized layers are not created or GPU memory remains too high.

Actions:

1. Install the optional package required by the selected `quant_type`: bitsandbytes for `bnb_*`, AutoAWQ for `awq_*`.
2. Do not combine `lora_layers` or `lora_embedding` with `freeze_encoder` or `freeze_decoder`.
3. When adding LoRA to a checkpoint, use `override_opts: true` and restate full architecture options.
4. Set non-empty `quant_layers` and a supported non-empty `quant_type`; either field alone is incomplete.
5. If using `use_ckpting: [lora]`, make sure LoRA parameters are actually present.
6. If using bitsandbytes optimizers such as `adamw8bit` or `pagedadamw8bit`, verify bitsandbytes imports in the target runtime.
7. Validate memory with a tiny batch before increasing `batch_size` or `accum_count`.

## Gradient checkpointing does not reduce memory or slows too much

Symptoms:

- Memory savings are smaller than expected.
- Training slows significantly.
- Checkpointing a module has no visible effect.

Actions:

1. Use only allowed values: `ffn`, `mha`, and `lora`.
2. Checkpoint modules with trainable gradients; frozen or non-existent modules do not help.
3. For LoRA-only fine-tuning, checkpointing `lora` may help, while `ffn` and `mha` may not if those base modules are frozen.
4. Measure one small run before committing to a long schedule.

## Transformer config asserts during model validation

Symptoms:

- Encoder and decoder hidden sizes differ.
- Absolute and relative position encodings are both enabled.
- SRU reports that GPU ranks are required.
- Shared embeddings fail validation.

Actions:

1. Keep `enc_hid_size` and `dec_hid_size` equal, or set `hidden_size` once.
2. Use either `position_encoding: true` or a nonzero `max_relative_positions`, not both.
3. For shared embeddings, use text models and a shared vocabulary.
4. For SRU, configure GPU ranks and confirm SRU dependencies are available.

## Training is extremely slow or runs out of memory

Actions:

1. For Transformer training, prefer `batch_type: tokens`, `normalization: tokens`, and gradient accumulation through `accum_count`.
2. Lower `batch_size` first, then increase `accum_count` to preserve the effective batch size.
3. Use `model_dtype: fp16` only in a GPU environment that supports the selected optimizer path.
4. Use LoRA and quantized layers for large checkpoint fine-tuning when optional dependencies are installed.
5. Use `n_sample` to dump and inspect transformed samples without starting full training.
6. Keep `report_every` small for tiny smoke runs, then increase it for long jobs.
