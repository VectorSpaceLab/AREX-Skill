# RACE Troubleshooting

Use this reference when XLNet RACE data loading, preprocessing, TPU setup, checkpoint loading, or memory planning fails.

## Quick triage table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| File-listing error under `data_dir` | Wrong RACE root or missing `split/level` directories. | Verify `RACE_DIR/{train,dev,test}/{middle,high}/`; if a level is intentionally absent, set the opposite filter. |
| JSON parsing/key error | Files are not RACE JSON article files or required fields are missing. | Check each file for `article`, `questions`, `options`, and `answers`; every question needs exactly four options and one A-D answer. |
| Zero or suspiciously tiny example count | Both `high_only` and `middle_only` selected, or the selected split/level is empty. | Use exactly one level filter or none; inspect `RACE_DIR/<eval_split>/<level>/`. |
| High-only/middle-only training seems to use full data | Training TFRecord cache was reused; train cache names do not include the level filter. | Use a separate `output_dir` for filtered training or set `--overwrite_data=True`. |
| `SentencePieceProcessor.Load` failure | Missing/wrong `spiece.model` path or inaccessible local file. | Point `--spiece_model_file` to the released model's `spiece.model`; use `--validate-local-paths` in the builder for local path checks. |
| Config load or model build failure | Missing/wrong `xlnet_config.json` or mismatch with checkpoint family. | Use config and SentencePiece files from the same released XLNet archive as the checkpoint. |
| Checkpoint initialization failure on TPU | `init_checkpoint` is local or TPU workers cannot read it. | Copy checkpoint shards to GCS and pass the checkpoint prefix, usually `gs://.../xlnet_model.ckpt`. |
| TPU resolver or connection error | TPU name, zone, project, or Cloud SDK credentials are missing/mismatched. | Add `--tpu-zone` and `--gcp-project`; confirm the TPU is running and in the same project/zone as the bucket and driver. |
| GCS permission error | TPU service account or driver account lacks read/write access. | Grant bucket read access for pretrained checkpoints and read/write access for `output_dir` and `model_dir`. |
| Local GPU out-of-memory | TPU recipe batch/length settings used on GPU. | Use TPU, switch to XLNet-Base, reduce `train_batch_size`, `eval_batch_size`, `max_seq_length`, and `max_qa_length`; start with batch size 1. |
| Accuracy cannot be compared to README numbers | Different split, level filter, checkpoint, sequence length, or hardware recipe. | Record exact command flags and cache paths; only compare like-for-like runs. |

## RACE layout failures

The loader expects this root shape:

```text
RACE_DIR/
  train/{middle,high}/...
  dev/{middle,high}/...
  test/{middle,high}/...
```

It calls a directory listing for each included level, so a missing directory is a hard error. If a user has only `high` data, set `--high_only=True`; if only `middle`, set `--middle_only=True`.

Each listed file must be a JSON object with aligned `questions`, `options`, and `answers` arrays. The options array must contain four candidates for every question because the feature builder always loops over exactly four choices.

## High/middle filter mistakes

The code does not enforce mutual exclusion between `high_only` and `middle_only`. If both are true:

- the `middle` level is skipped because `high_only` is true;
- the `high` level is skipped because `middle_only` is true;
- downstream behavior can become an empty dataset or confusing cache output.

The bundled builder prevents selecting both. If hand-editing a command, verify exactly one or zero filters are present.

## TFRecord cache confusion

By default, `run_race.py` reuses existing TFRecord files in `output_dir`. This is useful for repeated full runs but risky when changing filters or lengths.

- Changing `max_seq_length` changes the cache filename.
- Changing `eval_split` changes the eval cache filename.
- High-only and middle-only eval caches get `high.` or `middle.` prefixes.
- High-only and middle-only training caches do **not** get a prefix.

When changing training filters, use a new `output_dir` or add `--overwrite_data=True`.

## Missing model artifacts

The released cased XLNet archive provides three required artifact types:

- `xlnet_config.json`
- `spiece.model`
- TensorFlow checkpoint shards with prefix `xlnet_model.ckpt`

For TPU runs, the checkpoint prefix generally belongs on GCS, while config and SentencePiece can remain local because preprocessing and graph setup run on the driver. Keep `model_dir` separate from the released checkpoint directory so finetuned checkpoints do not overwrite or mix with pretrained artifacts.

## TPU and GCS setup absent

The TPU profiles require:

- `--use_tpu=True`
- a valid `--tpu` name;
- GCS `output_dir` and `model_dir` for generated TFRecords and checkpoints;
- a TPU-readable `init_checkpoint` prefix;
- optional `--tpu_zone` and `--gcp_project` when not inferred.

If no Cloud TPU/GCS runtime is available, do not present the v3-8 or v3-32 command as runnable. Use the memory-safe local fallback only for debugging data and flag plumbing.

## GPU memory and TPU-sized recipes

RACE has a special memory multiplier: one example contains four candidate sequences. Therefore:

```text
effective candidate sequences per step ~= train_batch_size * 4
```

The documented TPU recipes imply:

- v3-8: `train_batch_size=8` -> 32 candidate sequences at length 512.
- v3-32/pod: `train_batch_size=32` -> 128 candidate sequences at length 512.

These are not safe local GPU defaults. If the user asks for a GPU run:

1. Explain that the repository supplied no RACE GPU recipe and that the TPU settings target TPU memory.
2. Prefer XLNet-Base for debugging.
3. Start with `train_batch_size=1`, `eval_batch_size=1`, `max_seq_length=128` or `256`, and `max_qa_length=64`.
4. Use a small RACE subset to validate preprocessing and checkpoint loading.
5. Increase lengths/batches only after memory is measured.
6. Do not compare the result with documented TPU accuracy.

## Eval-only split diagnostics

For high-only or middle-only evaluation of a full-RACE model:

- Use `--do_train=False` / builder `--no-train`.
- Keep `--do_eval=True`.
- Set `--eval_split=dev` or `--eval_split=test` according to the available directory.
- Select exactly one level filter.
- Confirm `model_dir` points to the finetuned estimator checkpoint directory.

Evaluation pads examples to a multiple of `eval_batch_size`; padding examples have zero metric weight, so a non-divisible split size is expected and not by itself a bug.
