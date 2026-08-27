# RACE Workflows

Use this reference to choose and assemble XLNet RACE training/evaluation workflows. The bundled builder prints commands only; it does not run training, touch GCS, or start a TPU job.

## Workflow decision table

| User goal | Recommended route | Key settings |
| --- | --- | --- |
| Reproduce the smaller documented XLNet-Large RACE recipe | TPU v3-8 profile | `num_hosts=1`, `num_core_per_host=8`, `train_batch_size=8`, `eval_batch_size=32`, `max_seq_length=512`, `max_qa_length=128`. |
| Reproduce the stronger/paper-scale XLNet-Large RACE recipe | TPU v3-32/pod profile | `num_hosts=4`, `num_core_per_host=8`, `train_batch_size=32`, `eval_batch_size=32`, `max_seq_length=512`, `max_qa_length=128`. |
| Evaluate only high-school or middle-school RACE | Eval-only command with one level filter | Add `--no-train` and exactly one of `--high-only` or `--middle-only`; keep `model_dir` on the finetuned checkpoint directory. |
| Debug without TPU/GCS | Reduced local/GPU smoke recipe | Do not use the TPU batch sizes. Use XLNet-Base if available, `train_batch_size=1`, small `eval_batch_size`, shorter sequence lengths, and a tiny subset. Treat this as a smoke test, not a benchmark. |

## Prerequisites

Before generating a command, collect these paths and resources:

- `RACE_DIR`: unpacked RACE root with `train/dev/test` and `middle/high` subdirectories. See [data-formats.md](data-formats.md).
- `XLNET_DIR`: released cased XLNet checkpoint directory containing:
  - `xlnet_config.json`
  - `spiece.model`
  - TensorFlow checkpoint shards with prefix `xlnet_model.ckpt`
- `GS_ROOT`: writable Google Cloud Storage prefix, for example `gs://<bucket>/<prefix>`.
- `TPU_NAME`: Cloud TPU name visible to the TensorFlow runtime.
- Optional `tpu_zone` and `gcp_project` when the default Cloud SDK context is insufficient.

For TPU runs, local preprocessing reads `RACE_DIR`, `spiece.model`, and `xlnet_config.json` from the driver process, while `output_dir`, `model_dir`, and `init_checkpoint` should be GCS paths accessible to TPU workers.

## Generate a TPU v3-8 command

From this sub-skill directory, print the smaller TPU recipe:

```bash
python scripts/build_race_command.py tpu-v3-8 \
  --race-dir "${RACE_DIR}" \
  --model-config-path "${XLNET_DIR}/xlnet_config.json" \
  --spiece-model-file "${XLNET_DIR}/spiece.model" \
  --init-checkpoint "${GS_ROOT}/xlnet_cased_L-24_H-1024_A-16/xlnet_model.ckpt" \
  --gcs-root "${GS_ROOT}" \
  --tpu-name "${TPU_NAME}"
```

Default generated flags preserve the documented v3-8 template:

- `--use_tpu=True`
- `--num_hosts=1`
- `--num_core_per_host=8`
- `--train_batch_size=8`
- `--eval_batch_size=32`
- `--train_steps=12000`, `--warmup_steps=1000`, `--save_steps=1000`, `--iterations=1000`
- `--learning_rate=2e-5`, `--weight_decay=0`, `--adam_epsilon=1e-6`

## Generate a TPU v3-32/pod command

Print the larger pod recipe:

```bash
python scripts/build_race_command.py tpu-v3-32 \
  --race-dir "${RACE_DIR}" \
  --model-config-path "${XLNET_DIR}/xlnet_config.json" \
  --spiece-model-file "${XLNET_DIR}/spiece.model" \
  --init-checkpoint "${GS_ROOT}/xlnet_cased_L-24_H-1024_A-16/xlnet_model.ckpt" \
  --gcs-root "${GS_ROOT}" \
  --tpu-name "${TPU_NAME}"
```

The v3-32/pod template differs from v3-8 by using four hosts and a larger global train batch:

| Setting | v3-8 | v3-32/pod |
| --- | --- | --- |
| TPU topology | Single v3-8 | Pod slice / four hosts |
| `num_hosts` | 1 | 4 |
| `num_core_per_host` | 8 | 8 |
| Total cores/shards | 8 | 32 |
| `train_batch_size` | 8 | 32 |
| `eval_batch_size` | 32 | 32 |

The `train_batch_size` value is the number of RACE examples; each example contains four candidate sequences. Therefore the v3-32 recipe processes 128 candidate sequences per training batch.

## High-only or middle-only evaluation

To evaluate a finetuned model on only one RACE level, generate an eval-only command and select exactly one level filter:

```bash
python scripts/build_race_command.py tpu-v3-8 \
  --race-dir "${RACE_DIR}" \
  --model-config-path "${XLNET_DIR}/xlnet_config.json" \
  --spiece-model-file "${XLNET_DIR}/spiece.model" \
  --init-checkpoint "${GS_ROOT}/xlnet_cased_L-24_H-1024_A-16/xlnet_model.ckpt" \
  --gcs-root "${GS_ROOT}" \
  --model-dir "${GS_ROOT}/experiment/race" \
  --tpu-name "${TPU_NAME}" \
  --no-train \
  --high-only
```

Use `--middle-only` instead of `--high-only` for the middle-school split. Keep `--eval-split=dev` for dev-set evaluation or set `--eval-split=test` when the `test` split is present.

Important filtering details:

- A level filter affects every split loaded in that run. If `--do_train=True`, high-only means high-only training as well as high-only evaluation.
- For a full-RACE-trained model, use `--no-train` for split-specific evaluation.
- The eval TFRecord filenames include `high.` or `middle.` prefixes, but the training TFRecord filename does not. Use a separate `output_dir` or `--overwrite_data=True` for filtered training.

## Memory-safe local/GPU fallback

The repository did not provide a RACE GPU script. If a user tries to run a TPU-sized command on local GPU, do not only toggle `--use_tpu=False`; the batch and sequence footprint remains too large for common GPUs.

For a memory-safe debugging fallback:

- Prefer XLNet-Base rather than XLNet-Large if the goal is a local smoke test.
- Use `train_batch_size=1`; remember that this still builds four candidate sequences.
- Start with `eval_batch_size=1` or `2`.
- Reduce `max_seq_length` to `128` or `256` and `max_qa_length` to `64` for debugging, accepting truncation and lower accuracy.
- Use a tiny copied subset of RACE while validating the data pipeline.
- Keep `num_hosts=1` and `num_core_per_host=1` for one GPU; multi-GPU uses TensorFlow 1.x `MirroredStrategy` and is not equivalent to the TPU pod recipe.
- Do not report resulting accuracy as comparable to the documented TPU numbers.

## Output interpretation

Evaluation logs report at least:

- `eval_accuracy`: multiple-choice accuracy over real examples only.
- `eval_loss`: weighted mean loss; padding examples appended to complete the final batch have zero weight.

When comparing high-only, middle-only, and full-RACE results, record the exact split, level filter, checkpoint/model directory, sequence lengths, and batch sizes because cached TFRecords and truncation settings materially affect results.
