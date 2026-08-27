# `run_classifier.py` CLI reference

This reference summarizes the classification/regression flags that matter for the supported processors. Use `../scripts/build_classifier_command.py` to generate commands safely.

## Supported tasks

| `--task_name` | Type | Metric used by eval best-result sort | Required special flag |
| --- | --- | --- | --- |
| `mnli_matched` | 3-class sentence-pair classification | `eval_accuracy` | none |
| `mnli_mismatched` | 3-class sentence-pair classification | `eval_accuracy` | none |
| `sts-b` | sentence-pair regression | `eval_pearsonr` | `--is_regression=True` |
| `imdb` | binary single-document classification | `eval_accuracy` | none |
| `yelp5` | 5-class single-document classification | `eval_accuracy` | none |

Unsupported names raise `ValueError("Task not found: ...")` before training.

## Essential path flags

| Flag | Required when | Meaning |
| --- | --- | --- |
| `--data_dir` | all modes | Raw data root in the selected processor layout. |
| `--output_dir` | all modes | TFRecord cache directory. Created if missing. |
| `--model_dir` | all modes | Estimator working directory for fine-tuned checkpoints/events. Eval scans this directory. |
| `--model_config_path` | all modes | XLNet JSON config for the checkpoint/model variant. Released model zips use `xlnet_config.json`. |
| `--spiece_model_file` | all modes | SentencePiece model used for tokenization. |
| `--init_checkpoint` | normally train | Checkpoint prefix for variable initialization. Use a released checkpoint for fine-tuning; usually omit for eval/predict against `model_dir`. |
| `--predict_dir` | predict | Directory for `<task>.tsv` and `<task>.logits.json`. Created if missing. |
| `--predict_ckpt` | optional predict | Explicit checkpoint prefix for prediction. If omitted, Estimator uses the latest checkpoint in `model_dir`. |

## Mode flags

At least one mode flag must be true.

| Flag | Behavior |
| --- | --- |
| `--do_train=True` | Reads train examples, creates/reuses a train TFRecord in `output_dir`, and calls `estimator.train(..., max_steps=train_steps)`. |
| `--do_eval=True` | Reads dev or test examples, pads to a multiple of `eval_batch_size`, creates/reuses an eval TFRecord, evaluates checkpoints from `model_dir`, and logs best result. |
| `--do_predict=True` | Reads dev or test examples, creates/reuses a predict TFRecord, runs `estimator.predict`, and writes TSV/JSON outputs to `predict_dir`. |
| `--eval_split=dev|test` | Selects dev vs test reader for eval/predict. GLUE processors implement both; IMDB/Yelp use labeled dev/test files through `eval_split=dev` and do not implement a separate test reader. |
| `--eval_all_ckpt=True` | Eval every checkpoint with a `.index` file in `model_dir`; otherwise eval only the latest sorted checkpoint. |

### Eval-all-checkpoints details

Evaluation scans `model_dir` for checkpoint index files, strips the `.index` suffix, parses the global step from the text after the last dash, and sorts by step. With `--eval_all_ckpt=False`, only the last checkpoint is evaluated. With `--eval_all_ckpt=True`, all found checkpoints are evaluated and the best result is sorted by `eval_accuracy` or `eval_pearsonr` for STS-B.

This means checkpoint filenames must look like normal TensorFlow checkpoint prefixes such as `model.ckpt-1200.index`. Nonstandard names without a trailing numeric step can fail parsing.

## Backend and device flags

| Flag | CPU/GPU meaning | TPU meaning |
| --- | --- | --- |
| `--use_tpu` | `False`; uses `tf.estimator.Estimator`. | `True`; uses `tf.contrib.tpu.TPUEstimator`. |
| `--num_hosts` | Usually `1`. | Number of TPU hosts. |
| `--num_core_per_host` | Number of GPUs used by `MirroredStrategy`; `1` means single-device mode. | Cores per host; `8` for TPU v2/v3-8, `16` for larger v3 pod hosts. |
| `--master` | Optional TensorFlow master string. | Usually omitted when using TPU resolver flags. |
| `--tpu`, `--tpu_zone`, `--gcp_project`, `--tpu_job_name` | Not used. | Cloud TPU resolver/job settings. |
| `--iterations` | Included in TPU RunConfig; also set by README recipes. | Iterations per TPU training loop, clipped to `save_steps` when saving. |

GPU training note: when `num_core_per_host > 1`, `train_batch_size` is per GPU. Effective global batch is approximately `train_batch_size * num_core_per_host * num_hosts` for the documented single-host GPU use case.

Evaluation note: the documented workflow uses single-GPU evaluation. Multi-GPU eval requires careful data sharding and is easy to get wrong.

## Training and optimization flags

| Flag | Default in source | Meaning |
| --- | --- | --- |
| `--train_steps` | `1000` | Max train steps. |
| `--warmup_steps` | `0` | Linear warmup steps before decay. |
| `--learning_rate` | `1e-5` | Initial learning rate. |
| `--lr_layer_decay_rate` | `1.0` | Optional layer-wise decay multiplier. |
| `--min_lr_ratio` | `0.0` | Minimum learning-rate ratio for poly/cos decay. |
| `--clip` | `1.0` | Global norm clipping. |
| `--train_batch_size` | `8` | Train batch size; per GPU in multi-GPU mode. |
| `--weight_decay` | `0.0` | AdamW-style decay. Source does not support `weight_decay > 0` with multi-GPU training. |
| `--adam_epsilon` | `1e-8` | Adam epsilon. |
| `--decay_method` | `poly` | `poly` or `cos`. |
| `--save_steps` | `None` | Save checkpoint every N steps. Needed if later using `eval_all_ckpt` over multiple checkpoints. |
| `--max_save` | `0` | Keep all checkpoints when `0`; otherwise max checkpoint count. |

## Model and task flags

| Flag | Default in source | Meaning |
| --- | --- | --- |
| `--max_seq_length` | `128` | Fixed input length for tokenized features. Longer lengths are memory-expensive. |
| `--uncased` | `False` | Lowercase preprocessing before SentencePiece encoding. Released public models are cased. |
| `--is_regression` | `False` | Switches to regression loss, float labels, and Pearson correlation metric. Required for STS-B. |
| `--num_passes` | `1` | Repeats training examples during TFRecord creation, mainly to avoid TPU batch loss. |
| `--shuffle_buffer` | `2048` | Training shuffle buffer. |
| `--overwrite_data` | `False` | Recreate TFRecord cache even if a matching filename already exists. |
| `--cls_scope` | `None` | Optional classifier layer variable scope. |
| `--summary_type` | `last` | Sequence summary method used by the classifier head. |
| `--dropout`, `--dropatt` | `0.1`, `0.1` | Fine-tuning dropout settings. |
| `--use_summ_proj` | `True` | Whether to project the summary vector. |
| `--use_bfloat16` | `False` | Optional bfloat16 mode, typically TPU-specific. |

## Prediction output semantics

Prediction writes two files under `predict_dir`:

- `<task_name>.tsv`: header `index\tprediction`, then one prediction per example.
- `<task_name>.logits.json`: raw logits list for each example.

Label choice rules:

- One logit: emit the numeric logit, used by STS-B regression.
- Two logits: emit label 1 if `logits[1] - logits[0] > predict_threshold`, else label 0.
- More than two logits: emit the label with max logit.

## Command generator quick reference

```bash
python ../scripts/build_classifier_command.py --help
```

Useful presets:

| Preset | Distilled source | Defaults it sets |
| --- | --- | --- |
| `stsb-gpu-large` | README STS-B GPU recipe | `task_name=sts-b`, GPU backend, sequence length 128, per-GPU train batch 8, eval batch 8, LR `5e-5`, 1200 train steps, 120 warmup, 600 save steps, regression enabled. |
| `imdb-tpu-large` | README IMDB TPU recipe | `task_name=imdb`, TPU backend, sequence length 512, train batch 32, eval batch 8, LR `2e-5`, 4000 steps, 500 warmup/save, 500 iterations, eval-all-checkpoints. |
| `colab-imdb-gpu` | Colab IMDB GPU notebook | `task_name=imdb`, single-GPU backend, sequence length 128, train/eval batch 8, LR `2e-5`, 4000 steps, 500 warmup/save, 500 iterations, eval-all-checkpoints. |

Abseil help note: in some managed environments, `run_classifier.py --help` prints the help text but returns a nonzero status. Treat printed usage as the useful signal; do not use the source help exit code alone as a runtime failure.
