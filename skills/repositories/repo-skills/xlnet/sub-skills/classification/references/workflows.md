# Classification/regression workflows

This reference distills the supported `run_classifier.py` workflows. Use the bundled command generator in `../scripts/build_classifier_command.py` to create shell commands; it prints commands only and has no training, download, or filesystem side effects.

## Common setup decisions

Every workflow needs:

- Raw task data in the processor's expected layout (`data_dir`).
- Released XLNet model artifacts: `spiece.model`, `xlnet_config.json`, and the checkpoint prefix `xlnet_model.ckpt` with its TensorFlow checkpoint shard files.
- A preprocessing/cache directory (`output_dir`) that is separate from both raw data and checkpoints.
- A fine-tuning working directory (`model_dir`) for Estimator checkpoints and events.

Directory roles are not interchangeable:

| Path flag | Role | Common mistake |
| --- | --- | --- |
| `--data_dir` | Raw task files/directories consumed by a built-in processor. | Pointing it at the TFRecord cache or a parent directory that does not contain the expected filenames. |
| `--output_dir` | Generated TFRecord cache such as `spiece.model.len-128.train.tf_record`. | Reusing stale records after changing data, task, sequence length, SentencePiece model, or regression mode. |
| `--model_dir` | Fine-tuned checkpoints and TensorFlow event files. Eval scans this directory for `*.index` checkpoint files. | Setting it to the released checkpoint directory or to the same directory as `init_checkpoint`. |
| `--init_checkpoint` | Checkpoint prefix used to initialize variables, normally a released XLNet checkpoint for training. | Passing the released checkpoint during eval-all-checkpoints, causing confusion between pretrained and fine-tuned state. |
| `--predict_dir` | Prediction output destination. | Omitting it when `--do_predict=True`; prediction writes `<task>.tsv` and `<task>.logits.json`. |

## Mode patterns

| Mode | Flags generated | Uses which examples | Typical checkpoint source |
| --- | --- | --- | --- |
| `train` | `--do_train=True` | `processor.get_train_examples(data_dir)` | `--init_checkpoint` initializes from a released or chosen checkpoint; saves to `model_dir`. |
| `eval` | `--do_eval=True` | `get_dev_examples` by default; GLUE `get_test_examples` when `--eval_split=test`. | Scans `model_dir` and evaluates latest or all checkpoints. Normally omit `init_checkpoint`. |
| `predict` | `--do_predict=True` | Same selection as eval, then writes predictions. | Uses `--predict_ckpt` if set, otherwise Estimator's latest checkpoint from `model_dir`. |
| `train_eval` | Train then eval in one process. | Train set then dev/test set. | Initializes from `init_checkpoint`, saves/evaluates in `model_dir`. |

For long GPU workflows, prefer separate `train` then `eval` commands. This keeps multi-GPU training separate from single-GPU evaluation.

## STS-B regression on GPUs

STS-B is a sentence-pair regression task. Use `task_name=sts-b` and keep `--is_regression=True` in training, evaluation, and prediction commands.

Training template adapted from the XLNet README:

```bash
python scripts/build_classifier_command.py \
  --preset stsb-gpu-large \
  --mode train \
  --data-dir /path/to/GLUE/STS-B \
  --output-dir proc_data/sts-b \
  --model-dir exp/sts-b \
  --model-config-path /path/to/xlnet_config.json \
  --spiece-model-file /path/to/spiece.model \
  --init-checkpoint /path/to/xlnet_model.ckpt \
  --cuda-visible-devices 0,1,2,3
```

Evaluation of all saved checkpoints should scan `model_dir` and should not reuse the released checkpoint directory as `model_dir`:

```bash
python scripts/build_classifier_command.py \
  --preset stsb-gpu-large \
  --mode eval \
  --data-dir /path/to/GLUE/STS-B \
  --output-dir proc_data/sts-b \
  --model-dir exp/sts-b \
  --model-config-path /path/to/xlnet_config.json \
  --spiece-model-file /path/to/spiece.model \
  --eval-all-ckpt \
  --cuda-visible-devices 0
```

Expected signal: logs report `eval_pearsonr` and `eval_loss`; with `--eval_all_ckpt=True`, the script sorts by `eval_pearsonr` and logs a best checkpoint. The README reported approximately `eval_pearsonr 0.916+` for the XLNet-Large multi-GPU recipe.

## MNLI matched and mismatched

Use the GLUE MNLI directory as `data_dir`.

- `task_name=mnli_matched` reads `train.tsv`, `dev_matched.tsv`, and `test_matched.tsv`.
- `task_name=mnli_mismatched` reads the same `train.tsv` but evaluates/predicts on `dev_mismatched.tsv` or `test_mismatched.tsv`.
- Labels are `contradiction`, `entailment`, and `neutral`.

Typical pattern:

1. Fine-tune with `mnli_matched` or `mnli_mismatched`; both use `train.tsv`.
2. Evaluate the same `model_dir` twice, once with `task_name=mnli_matched` and once with `task_name=mnli_mismatched`.
3. Use separate `predict_dir` subdirectories if generating both matched and mismatched test outputs.

Example evaluation command for the mismatched dev split:

```bash
python scripts/build_classifier_command.py \
  --task-name mnli_mismatched \
  --mode eval \
  --backend gpu \
  --cuda-visible-devices 0 \
  --data-dir /path/to/GLUE/MNLI \
  --output-dir proc_data/mnli \
  --model-dir exp/mnli \
  --model-config-path /path/to/xlnet_config.json \
  --spiece-model-file /path/to/spiece.model \
  --eval-batch-size 8
```

## IMDB TPU recipe

The README's high-accuracy IMDB recipe uses XLNet-Large, sequence length 512, and a Cloud TPU v3-8. Raw IMDB files are local for preprocessing, while `output_dir`, `model_dir`, and checkpoint/config paths may live in cloud storage.

```bash
python scripts/build_classifier_command.py \
  --preset imdb-tpu-large \
  --mode train_eval \
  --data-dir /path/to/aclImdb \
  --output-dir gs://bucket/proc_data/imdb \
  --model-dir gs://bucket/exp/imdb \
  --model-config-path gs://bucket/xlnet_cased_L-24_H-1024_A-16/xlnet_config.json \
  --spiece-model-file /path/to/xlnet_cased_L-24_H-1024_A-16/spiece.model \
  --init-checkpoint gs://bucket/xlnet_cased_L-24_H-1024_A-16/xlnet_model.ckpt \
  --tpu my-tpu-name
```

Notes:

- `--max_seq_length=512` is important for the strongest README IMDB result, but it is memory intensive.
- On TPU, `train_batch_size` is the TPUEstimator train batch size and `num_core_per_host=8` for a v2/v3-8 worker.
- Local `data_dir` and `spiece_model_file` are faster for preprocessing even if checkpoints are in cloud storage.

## IMDB Colab/GPU recipe

The Colab notebook demonstrates a constrained GPU workflow. It downloads the cased large released model, downloads `aclImdb`, and runs train+eval locally with shorter sequences.

Use this preset to reproduce the command shape without bundling or rerunning the notebook:

```bash
python scripts/build_classifier_command.py \
  --preset colab-imdb-gpu \
  --mode train_eval \
  --data-dir aclImdb \
  --output-dir proc_data/imdb \
  --model-dir exp/imdb \
  --model-config-path xlnet_cased_L-24_H-1024_A-16/xlnet_config.json \
  --spiece-model-file xlnet_cased_L-24_H-1024_A-16/spiece.model \
  --init-checkpoint xlnet_cased_L-24_H-1024_A-16/xlnet_model.ckpt \
  --cuda-visible-devices 0
```

The notebook used `max_seq_length=128`, `train_batch_size=8`, `eval_batch_size=8`, `train_steps=4000`, `warmup_steps=500`, `save_steps=500`, and `iterations=500`. It reported about 1 hour 11 minutes of training, about 2.5 hours of evaluation, and accuracy around `0.92416`; this is lower than the README TPU result and is intended as a practical GPU example.

## Yelp-5 review classification

Yelp-5 expects CSV files rather than GLUE TSV or IMDB folders:

```bash
python scripts/build_classifier_command.py \
  --task-name yelp5 \
  --mode train_eval \
  --backend gpu \
  --cuda-visible-devices 0 \
  --data-dir /path/to/yelp_review_full_csv \
  --output-dir proc_data/yelp5 \
  --model-dir exp/yelp5 \
  --model-config-path /path/to/xlnet_config.json \
  --spiece-model-file /path/to/spiece.model \
  --init-checkpoint /path/to/xlnet_model.ckpt \
  --max-seq-length 512 \
  --train-batch-size 4 \
  --eval-batch-size 8 \
  --learning-rate 2e-5 \
  --train-steps 4000 \
  --warmup-steps 500 \
  --save-steps 500
```

For smaller GPUs, reduce `--max-seq-length` first or reduce `--train-batch-size`. The built-in Yelp processor uses `test.csv` as the dev/eval file.

## Prediction outputs

Prediction mode requires `--predict_dir`. It writes:

- `<task_name>.tsv` with columns `index` and `prediction`.
- `<task_name>.logits.json` containing raw logits for every predicted example.

For binary tasks, `predict_threshold` compares `logits[1] - logits[0]`; for multi-class tasks, the max-logit label is emitted; for STS-B regression, the single logit is emitted as a numeric prediction. Use `--eval_split=test` only for processors that implement a test reader; GLUE processors do, while IMDB/Yelp use their labeled dev/test data via `eval_split=dev`.
