---
name: squad-qa
description: "Operate XLNet SQuAD 1.1/2.0 preprocessing, fine-tuning,
  prediction, and threshold evaluation workflows through run_squad.py."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XLNet SQuAD QA operating sub-skill

Use this sub-skill when the task is span-extraction question answering with XLNet through `run_squad.py`: SQuAD JSON preprocessing, SQuAD 1.1/2.0 fine-tuning, prediction, prediction-cache management, n-best span decoding, or SQuAD 2.0 no-answer threshold evaluation.

## Route elsewhere

- RACE or other four-choice reading-comprehension tasks -> `race-reading-comprehension`.
- GLUE, IMDB, Yelp, or general classification/regression -> `classification`.
- Direct graph/API changes, custom losses, or checkpoint internals -> `model-api`.

## Minimal inputs to collect

1. XLNet runtime with legacy TensorFlow 1.x, SentencePiece, and `run_squad.py` available.
2. Model artifacts: `xlnet_config.json`, `spiece.model`, and a checkpoint for training (`--init_checkpoint`) or a fine-tuned checkpoint under `--model_dir` for prediction-only.
3. SQuAD-style JSON: training JSON for preprocessing/fine-tuning and prediction JSON for dev/test prediction.
4. Separate directories for feature cache (`--output_dir`), fine-tuned checkpoints (`--model_dir`), and prediction JSON outputs (`--predict_dir`).
5. Backend choice: GPU base fallback, Cloud TPU large recipe, or prediction-only.

## Operating flow

1. Confirm the data shape in [data-formats.md](references/data-formats.md). For training, each QA must include `is_impossible`; SQuAD 1.1 data usually needs this field added with `false`.
2. Generate a command with [scripts/build_squad_command.py](scripts/build_squad_command.py). The builder prints commands only and never executes them.
3. Run preprocessing first when training: `--do_prepro=True` writes training TFRecords into `--output_dir`. Use `--num_proc`/`--proc_id` or the builder's `--emit-all-proc-ids` for parallel preprocessing.
4. Run GPU or TPU fine-tuning/evaluation, or `predict-only` against a fine-tuned `--model_dir`. Prediction creates or reuses eval TFRecord/feature cache in `--output_dir` and writes `predictions.json`, `nbest_predictions.json`, and `null_odds.json` in `--predict_dir`.
5. Read the logged SQuAD metrics. `run_squad.py` computes best SQuAD 2.0 thresholds from `null_odds.json` and reports keys such as `best_exact`, `best_f1`, `best_*_thresh`, `has_ans_exact`, and `has_ans_f1`.

## Quick command-builder examples

Preprocess one SQuAD training split:

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode prepro \
  --spiece-model-file xlnet_cased/spiece.model \
  --train-file data/squad/train-v2.0.json \
  --output-dir proc_data/squad
```

Generate the GPU base training/prediction recipe:

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode gpu-base \
  --model-config-path xlnet_cased_base/xlnet_config.json \
  --spiece-model-file xlnet_cased_base/spiece.model \
  --init-checkpoint xlnet_cased_base/xlnet_model.ckpt \
  --output-dir proc_data/squad \
  --model-dir experiment/squad_base \
  --train-file data/squad/train-v2.0.json \
  --predict-file data/squad/dev-v2.0.json \
  --predict-dir predictions/squad_base
```

Generate a TPU large recipe when TPU and GCS are available:

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py \
  --mode tpu-large \
  --tpu my-tpu \
  --model-config-path xlnet_cased_large/xlnet_config.json \
  --spiece-model-file xlnet_cased_large/spiece.model \
  --init-checkpoint gs://bucket/xlnet_cased_large/xlnet_model.ckpt \
  --output-dir gs://bucket/proc_data/squad \
  --model-dir gs://bucket/experiment/squad_large \
  --train-file data/squad/train-v2.0.json \
  --predict-file data/squad/dev-v2.0.json \
  --predict-dir gs://bucket/predictions/squad_large
```

For detailed recipes, CLI flags, and failure recovery, use:

- [workflows.md](references/workflows.md)
- [data-formats.md](references/data-formats.md)
- [cli-reference.md](references/cli-reference.md)
- [troubleshooting.md](references/troubleshooting.md)
