# SQuAD workflows for XLNet `run_squad.py`

These workflows cover SQuAD 1.1/2.0 span QA with `run_squad.py`. The bundled command builder prints commands and does not run them:

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py --help
```

Run printed commands from an XLNet runtime where `run_squad.py` and the repo modules are importable.

## Workflow 1: preprocess training data

Use preprocessing before training. It reads `--train_file`, tokenizes with SentencePiece, maps raw character answer positions to token positions, and writes training TFRecords into `--output_dir`.

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode prepro \
  --spiece-model-file xlnet_cased_L-24_H-1024_A-16/spiece.model \
  --train-file data/squad/train-v2.0.json \
  --output-dir proc_data/squad \
  --max-seq-length 512 \
  --max-query-length 64 \
  --doc-stride 128
```

The generated command includes:

- `--use_tpu=False`
- `--do_prepro=True`
- `--spiece_model_file=...`
- `--train_file=...`
- `--output_dir=...`
- sequence/query/stride settings

Expected training cache file pattern:

```text
<spiece_basename>.<proc_id>.slen-<max_seq_length>.qlen-<max_query_length>.train.tf_record
```

### Parallel preprocessing

Preprocessing can be slow because it aligns raw character answer positions to SentencePiece positions. Split work with `--num_proc` and `--proc_id`; each process writes a distinct TFRecord because `proc_id` is embedded in the file name.

Print all process commands:

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode prepro \
  --spiece-model-file xlnet_cased_L-24_H-1024_A-16/spiece.model \
  --train-file data/squad/train-v2.0.json \
  --output-dir proc_data/squad \
  --num-proc 8 \
  --emit-all-proc-ids
```

Run all printed commands with the same `--output_dir`. Do not reuse a partial output directory after changing `max_seq_length`, `max_query_length`, or the SentencePiece model unless you also pass `--overwrite_data` for later eval-cache refreshes or clean the old cache.

## Workflow 2: GPU base fine-tuning and dev prediction

Use this when TPU/GCS is unavailable or when a smaller XLNet-Base setup is acceptable. The preserved base recipe assumes multiple GPUs and sequence length 512; if memory is tight, reduce `--train-batch-size`, `--predict-batch-size`, or `--max-seq-length` and expect possible quality changes.

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode gpu-base \
  --model-config-path xlnet_cased_L-12_H-768_A-12/xlnet_config.json \
  --spiece-model-file xlnet_cased_L-12_H-768_A-12/spiece.model \
  --init-checkpoint xlnet_cased_L-12_H-768_A-12/xlnet_model.ckpt \
  --output-dir proc_data/squad \
  --model-dir experiment/squad_base \
  --train-file data/squad/train-v2.0.json \
  --predict-file data/squad/dev-v2.0.json \
  --predict-dir predictions/squad_base
```

Default GPU base hyperparameters printed by the builder:

| Setting | Value |
| --- | --- |
| `--use_tpu` | `False` |
| `--num_hosts` | `1` |
| `--num_core_per_host` | `3` (interpreted as GPU count) |
| `--max_seq_length` | `512` |
| `--do_train` / `--do_predict` | `True` / `True` |
| `--train_batch_size` | `8` |
| `--predict_batch_size` | `32` |
| `--learning_rate` | `2e-5` |
| `--adam_epsilon` | `1e-6` |
| `--iterations` | `1000` |
| `--save_steps` | `1000` |
| `--train_steps` | `12000` |
| `--warmup_steps` | `1000` |

Training reads preprocessed training records from `--output_dir`; prediction reads `--predict_file`, builds or reuses eval cache in `--output_dir`, and writes prediction JSON files to `--predict_dir`.

## Workflow 3: TPU large fine-tuning and dev prediction

Use this only when Cloud TPU and GCS paths are configured. The large recipe preserves the high-performing XLNet-Large SQuAD setup with sequence length 512 and training batch size 48.

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode tpu-large \
  --tpu my-tpu \
  --model-config-path xlnet_cased_L-24_H-1024_A-16/xlnet_config.json \
  --spiece-model-file xlnet_cased_L-24_H-1024_A-16/spiece.model \
  --init-checkpoint gs://my-bucket/xlnet_cased_L-24_H-1024_A-16/xlnet_model.ckpt \
  --output-dir gs://my-bucket/proc_data/squad \
  --model-dir gs://my-bucket/experiment/squad_large \
  --train-file data/squad/train-v2.0.json \
  --predict-file data/squad/dev-v2.0.json \
  --predict-dir gs://my-bucket/predictions/squad_large
```

Default TPU large hyperparameters printed by the builder:

| Setting | Value |
| --- | --- |
| `--use_tpu` | `True` |
| `--num_hosts` | `1` |
| `--num_core_per_host` | `8` |
| `--max_seq_length` | `512` |
| `--do_train` / `--do_predict` | `True` / `True` |
| `--train_batch_size` | `48` |
| `--predict_batch_size` | `32` |
| `--learning_rate` | `3e-5` |
| `--adam_epsilon` | `1e-6` |
| `--iterations` | `1000` |
| `--save_steps` | `1000` |
| `--train_steps` | `8000` |
| `--warmup_steps` | `1000` |

For TPU mode, keep `--output_dir`, `--init_checkpoint`, `--model_dir`, and `--predict_dir` on GCS unless your TPU runtime is explicitly configured to read another filesystem. If TPU/GCS is not ready, use the GPU base fallback instead of trying to run the TPU large recipe locally.

## Workflow 4: prediction-only from a fine-tuned model

Use this when a model has already been fine-tuned and `--model_dir` contains checkpoints. Do not pass a pretrained `--init_checkpoint` for prediction-only; `run_squad.py` logs that `init_checkpoint` is not used in predict mode.

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode predict-only \
  --model-config-path xlnet_cased_L-12_H-768_A-12/xlnet_config.json \
  --spiece-model-file xlnet_cased_L-12_H-768_A-12/spiece.model \
  --output-dir proc_data/squad_eval_cache \
  --model-dir experiment/squad_base \
  --predict-file data/squad/dev-v2.0.json \
  --predict-dir predictions/squad_base_dev
```

The generated command includes `--do_train=False` and `--do_predict=True`. Prediction creates these files under `--predict_dir`:

- `predictions.json`: best non-null answer text per question id.
- `nbest_predictions.json`: n-best span candidates with probabilities and log-probabilities.
- `null_odds.json`: no-answer score used for SQuAD 2.0 threshold search.

## Workflow 5: threshold evaluation interpretation

During prediction, `run_squad.py` loads the original prediction JSON, writes predictions, and calls the bundled SQuAD 2.0 evaluator functions. It logs a line containing the metrics returned by threshold search.

Important keys:

| Key | Meaning |
| --- | --- |
| `best_exact` | Best exact-match percentage after no-answer threshold search. |
| `best_exact_thresh` | Threshold on `null_odds.json` that produced `best_exact`. |
| `best_f1` | Best F1 percentage after no-answer threshold search; default `target_eval_key` value. |
| `best_f1_thresh` | Threshold on `null_odds.json` that produced `best_f1`. |
| `has_ans_exact` | Exact score on answerable questions only. |
| `has_ans_f1` | F1 score on answerable questions only; the code comment for `target_eval_key` suggests this for one model variant. |

`--target_eval_key` is declared by the CLI, defaults to `best_f1`, and is useful for wrapper conventions. The current `run_squad.py` implementation logs all returned metrics rather than using this flag internally for checkpoint selection.

## Decision guide

| User situation | Use |
| --- | --- |
| Raw SQuAD training JSON and no TFRecords yet | `prepro` first, optionally parallelized. |
| TPU/GCS unavailable | `gpu-base`; reduce batch sizes if OOM. |
| TPU v3-8 and GCS configured, aiming for large-model recipe | `tpu-large`. |
| Fine-tuned checkpoint already exists | `predict-only` with `--model_dir`. |
| SQuAD 1.1 training JSON lacks `is_impossible` | Add `is_impossible: false` to each QA before preprocessing. |
| User asks about RACE multiple choice | Route to `race-reading-comprehension`. |
