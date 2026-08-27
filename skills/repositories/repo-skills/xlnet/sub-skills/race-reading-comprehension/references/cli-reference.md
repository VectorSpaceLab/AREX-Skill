# RACE CLI Reference

This reference summarizes the `run_race.py` flags that matter for RACE multiple-choice workflows and the bundled dry command builder.

## Bundled command builder

Use the bundled helper to print a shell-quoted command. It never executes the command.

```bash
python scripts/build_race_command.py --help
python scripts/build_race_command.py tpu-v3-8 --help
python scripts/build_race_command.py tpu-v3-32 --help
```

Required TPU-profile inputs:

| Builder option | Meaning |
| --- | --- |
| `tpu-v3-8` or `tpu-v3-32` | Selects the adapted template. |
| `--race-dir` | Local unpacked RACE root. |
| `--model-config-path` | Local `xlnet_config.json` from the released model archive. |
| `--spiece-model-file` | Local `spiece.model` from the released model archive. |
| `--init-checkpoint` | TPU-readable checkpoint prefix, usually `gs://.../xlnet_model.ckpt`. |
| `--gcs-root` | GCS root used to derive default `output_dir` and `model_dir`. |
| `--tpu-name` | Cloud TPU name. |

Common builder overrides:

| Builder option | Effect |
| --- | --- |
| `--output-dir` | Override default `<gcs-root>/proc_data/race`. Must be GCS for TPU profiles. |
| `--model-dir` | Override default `<gcs-root>/experiment/race`. Must be GCS for TPU profiles. |
| `--tpu-zone`, `--gcp-project` | Add Cloud TPU resolver metadata when default credentials/context are insufficient. |
| `--eval-split {dev,test}` | Select evaluation split. Default is `dev`. |
| `--high-only` / `--middle-only` | Add exactly one level filter. The builder makes them mutually exclusive. |
| `--no-train` / `--no-eval` | Turn off a phase. At least one phase must remain enabled. |
| `--max-seq-length`, `--max-qa-length` | Override length defaults. |
| `--train-batch-size`, `--eval-batch-size` | Override profile batch sizes deliberately. |
| `--overwrite-data` | Regenerate TFRecords instead of reusing cache. |
| `--validate-local-paths` | Check local `race_dir`, `model_config_path`, and `spiece_model_file` before printing. |
| `--extra-flag FLAG` | Append an additional raw `run_race.py` flag such as `--master=grpc://...`. Repeat as needed. |
| `--one-line` | Print one shell line instead of a backslash-wrapped command. |

## Adapted TPU profile defaults

| Generated flag | `tpu-v3-8` | `tpu-v3-32` | Notes |
| --- | --- | --- | --- |
| `--use_tpu` | `True` | `True` | Both are TPU-specific. |
| `--num_hosts` | `1` | `4` | v3-32/pod uses four hosts in the source template. |
| `--num_core_per_host` | `8` | `8` | Total shards are `num_hosts * num_core_per_host`. |
| `--train_batch_size` | `8` | `32` | Number of RACE examples, not candidate sequences. |
| `--eval_batch_size` | `32` | `32` | Evaluation pads examples to a multiple of this value. |
| `--max_seq_length` | `512` | `512` | Per candidate sequence. |
| `--max_qa_length` | `128` | `128` | Question-answer part is truncated from the left if too long. |
| `--train_steps` | `12000` | `12000` | Documented RACE template value. |
| `--warmup_steps` | `1000` | `1000` | Documented RACE template value. |
| `--save_steps` | `1000` | `1000` | Also caps `iterations` in `run_race.py`. |
| `--iterations` | `1000` | `1000` | TPU loop iterations. |
| `--learning_rate` | `2e-5` | `2e-5` | Documented RACE template value. |
| `--weight_decay` | `0` | `0` | Documented RACE template value. |
| `--adam_epsilon` | `1e-6` | `1e-6` | Documented RACE template value. |

## Core `run_race.py` flags

### Paths and model artifacts

| Flag | Required for common runs | Meaning |
| --- | --- | --- |
| `--data_dir` | Yes | RACE root containing split/level directories. |
| `--output_dir` | Yes | TFRecord cache directory. Use GCS for TPU runs. |
| `--model_dir` | Yes | Estimator checkpoint/event directory. Use a directory separate from the released pretrained checkpoint. |
| `--spiece_model_file` | Yes | SentencePiece model file. Used by local preprocessing. |
| `--model_config_path` | Yes | XLNet config JSON. |
| `--init_checkpoint` | Usually | Checkpoint prefix for initialization. For TPU runs this should be readable by TPU workers, usually a GCS path. |
| `--overwrite_data` | Optional | Regenerate TFRecords even when matching cache files already exist. |

### Hardware and distribution

| Flag | Meaning |
| --- | --- |
| `--use_tpu` | Use `tf.contrib.tpu.TPUEstimator` when true. Without TPU it falls back to TensorFlow Estimator. |
| `--tpu` | TPU name. |
| `--tpu_zone` | TPU zone when not inferred from environment. |
| `--gcp_project` | GCP project when not inferred from environment. |
| `--master` | TensorFlow master for non-TPU/custom runtime. |
| `--num_hosts` | Number of TPU hosts. |
| `--num_core_per_host` | TPU cores per host; for non-TPU multi-GPU it is used as number of GPUs for `MirroredStrategy`. |
| `--iterations` | Iterations per TPU training loop. If `save_steps` is set, `run_race.py` uses `min(iterations, save_steps)`. |

### Training

| Flag | Default | Meaning |
| --- | --- | --- |
| `--do_train` | `False` | Enable training. At least one of train/eval must be true. |
| `--train_batch_size` | `8` | Number of RACE examples. One example is four candidate sequences. |
| `--train_steps` | `12000` | Maximum training steps. |
| `--warmup_steps` | `0` | Learning-rate warmup steps. Templates use `1000`. |
| `--learning_rate` | `2e-5` | Initial learning rate. |
| `--lr_layer_decay_rate` | `1.0` | Layer-wise learning-rate decay. |
| `--min_lr_ratio` | `0.0` | Minimum ratio for cosine decay. |
| `--clip` | `1.0` | Gradient clipping. |
| `--weight_decay` | `0.0` | Weight decay. Templates use `0`. |
| `--adam_epsilon` | `1e-6` | Adam epsilon. |
| `--decay_method` | `poly` | Learning-rate decay method, `poly` or `cos`. |
| `--save_steps` | unset | Save checkpoint every N steps. Templates use `1000`. |
| `--max_save` | `0` | Max checkpoints to keep; `0` saves all. |
| `--shuffle_buffer` | `2048` | Training input shuffle buffer. |

### Evaluation

| Flag | Default | Meaning |
| --- | --- | --- |
| `--do_eval` | `False` | Enable evaluation. |
| `--eval_split` | `dev` | Split subdirectory to evaluate, intended as `dev` or `test`. |
| `--eval_batch_size` | `32` | Number of RACE examples per eval batch. Fake padding examples are added until divisible by this size. |
| `--high_only` | `False` | Skip `middle` examples for any split loaded in this run. |
| `--middle_only` | `False` | Skip `high` examples for any split loaded in this run. |

### Length, tokenization, and model behavior

| Flag | Default | Meaning |
| --- | --- | --- |
| `--max_seq_length` | `512` | Per-candidate sequence length after context/question-answer packing. |
| `--max_qa_length` | `128` | Maximum tokenized question-answer length before packing. |
| `--uncased` | `False` | Lowercase input during preprocessing when true. Released XLNet RACE recipes use cased models. |
| `--dropout`, `--dropatt` | `0.1`, `0.1` | Dropout rates. |
| `--summary_type` | `last` | Sequence summary method used by the model. |
| `--use_summ_proj` | `True` | Whether to project the sequence summary. |
| `--use_bfloat16` | `False` | bfloat16 mode. |
| `--clamp_len` | `-1` | Attention relative-position clamp length. |

## Boolean flag style

The underlying Abseil flags accept explicit values, for example `--do_train=True`, `--do_eval=False`, and `--uncased=False`. The command builder emits explicit boolean values to make generated commands auditable.

## Batch-size reminder

`train_batch_size=1` is not one token sequence. It is one RACE question/example containing four packed candidate sequences. Multiply by four when estimating memory pressure.
