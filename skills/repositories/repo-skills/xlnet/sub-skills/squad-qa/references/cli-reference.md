# SQuAD CLI reference

`run_squad.py` is an Abseil/TensorFlow 1.x CLI. Import or inspect it in a separate Python process from other XLNet CLI modules because multiple modules define overlapping Abseil flags.

Use the local command builder to generate commands safely:

```bash
python sub-skills/squad-qa/scripts/build_squad_command.py --help
```

## Command-builder modes

| Mode | Purpose | Required path flags |
| --- | --- | --- |
| `prepro` | Write training TFRecords from `--train_file`. | `--spiece-model-file`, `--train-file`, `--output-dir` |
| `gpu-base` | XLNet-Base GPU training plus prediction recipe. | `--model-config-path`, `--spiece-model-file`, `--init-checkpoint`, `--output-dir`, `--model-dir`, `--train-file`, `--predict-file`, `--predict-dir` |
| `tpu-large` | XLNet-Large Cloud TPU training plus prediction recipe. | Same as `gpu-base`, plus `--tpu`; GCS expected for output/checkpoint/model/predict directories |
| `predict-only` | Predict/evaluate from checkpoints already in `--model_dir`. | `--model-config-path`, `--spiece-model-file`, `--output-dir`, `--model-dir`, `--predict-file`, `--predict-dir` |

The builder never executes generated commands. It validates required arguments, quotes values, and prints a shell-ready `python run_squad.py ...` command.

## Builder options

| Builder flag | Effect |
| --- | --- |
| `--python` | Python executable printed at the beginning of the command; default `python`. |
| `--runner` | Path printed for `run_squad.py`; default `run_squad.py`. |
| `--mode` | One of `prepro`, `gpu-base`, `tpu-large`, `predict-only`. |
| `--emit-all-proc-ids` | With `--mode prepro` and `--num-proc N`, print N commands for `proc_id=0..N-1`. |
| `--allow-non-gcs-tpu-paths` | Bypass the builder's TPU GCS-path guard when a custom TPU runtime can read non-GCS paths. |
| `--extra-arg=--flag=value` | Append an additional `run_squad.py` flag. Use only for known flags not surfaced by the builder. |

## `run_squad.py` preprocessing flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--do_prepro` | `False` | If `True`, perform preprocessing only and return before training/prediction. |
| `--num_proc` | `1` | Number of preprocessing workers. The script selects `train_examples[proc_id::num_proc]`. |
| `--proc_id` | `0` | Worker id. Must be unique per parallel process and smaller than `num_proc`. |

## Model and artifact flags

| Flag | Default | Required for | Notes |
| --- | --- | --- | --- |
| `--model_config_path` | `None` | train/predict | Path to `xlnet_config.json`. |
| `--spiece_model_file` | `""` | prepro/train/predict | SentencePiece model. Missing file causes tokenizer load failure. |
| `--init_checkpoint` | `None` | training init | Pretrained or fine-tuned checkpoint for initialization. Ignored in `PREDICT` mode by the model function. |
| `--init_global_vars` | `False` | special checkpoint init | If true, initialize all global vars instead of trainable vars only. |
| `--output_dir` | `""` | prepro/train/predict | Training TFRecord and eval-cache directory. Must not be empty. |
| `--predict_dir` | `""` | prediction | Prediction JSON output directory. Must not be empty when `--do_predict=True`. |
| `--model_dir` | `""` | train/predict | Estimator checkpoint directory. Prediction-only loads latest checkpoint from here. |
| `--train_file` | `""` | prepro; conventionally train mode | Raw SQuAD training JSON. |
| `--predict_file` | `""` | prediction | Raw SQuAD dev/test JSON. |
| `--overwrite_data` | `False` | cache refresh | If false, existing eval TFRecord and feature pickle are reused. |

## Data preprocessing configuration

| Flag | Default | Notes |
| --- | --- | --- |
| `--max_seq_length` | `512` | Total feature length including question, passage window, and special tokens. Large values improve long context coverage but increase memory. |
| `--max_query_length` | `64` | Questions longer than this are truncated. |
| `--doc_stride` | `128` | Sliding-window stride for long contexts. Smaller stride increases overlap and feature count. |
| `--max_answer_length` | `64` | Maximum decoded answer span length. |
| `--uncased` | `False` | Use `False` for cased XLNet checkpoints; only set true with matching uncased assets. |

## Backend and distributed flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--use_tpu` | `False` | Switches to TPUEstimator when true. Use GPU base fallback if TPU/GCS is unavailable. |
| `--num_hosts` | `1` | Number of TPU hosts; for GPU mode, keep 1 unless customizing distribution. |
| `--num_core_per_host` | `8` | TPU cores per host; in GPU mode this is interpreted as the number of GPUs used. |
| `--tpu` | `None` | TPU name for Cloud TPU. |
| `--tpu_zone` | `None` | TPU zone. |
| `--gcp_project` | `None` | GCP project. |
| `--master` | `None` | TensorFlow master override. |
| `--tpu_job_name` | `None` | TPU worker job name. |
| `--iterations` | `1000` | Iterations per TPU training loop; script caps it to `save_steps` when `save_steps` is set. |

## Training flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--do_train` | `True` | At least one of `--do_train` or `--do_predict` must be true unless `--do_prepro=True`. |
| `--train_batch_size` | `48` | Global training batch size for TPUEstimator; GPU recipe uses 8 with 3 GPUs in the distilled base recipe. |
| `--train_steps` | `8000` | Number of training steps. GPU base recipe uses 12000. |
| `--warmup_steps` | `0` | GPU/TPU recipes use 1000. |
| `--save_steps` | `None` | Checkpoint period. Recipes use 1000. |
| `--max_save` | `5` | Maximum checkpoints to retain; 0 saves all. |
| `--shuffle_buffer` | `2048` | Training record shuffle buffer. |

## Optimization and model-regularization flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--learning_rate` | `3e-5` | GPU base recipe uses `2e-5`; TPU large uses `3e-5`. |
| `--min_lr_ratio` | `0.0` | Minimum learning-rate ratio for cosine decay. |
| `--clip` | `1.0` | Gradient clipping. |
| `--weight_decay` | `0.00` | Weight decay. |
| `--adam_epsilon` | `1e-6` | Adam epsilon used by recipes. |
| `--decay_method` | `poly` | `poly` or `cos`. |
| `--lr_layer_decay_rate` | `0.75` | Layer-wise learning-rate decay factor. |
| `--dropout` | `0.1` | Dropout rate. |
| `--dropatt` | `0.1` | Attention dropout. |
| `--clamp_len` | `-1` | Relative-position clamp length. |
| `--summary_type` | `last` | Sequence summary method, mostly relevant to shared model helpers. |
| `--use_bfloat16` | `False` | TPU bfloat16 option. |
| `--init`, `--init_std`, `--init_range` | `normal`, `0.02`, `0.1` | Parameter initialization controls. |

## Prediction and decoding flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--do_predict` | `False` | Enables prediction/evaluation. |
| `--predict_batch_size` | `32` | Reduce for memory issues. |
| `--n_best_size` | `5` | Number of final n-best text candidates written per question. |
| `--start_n_top` | `5` | Beam size for start positions. Larger values increase decode work. |
| `--end_n_top` | `5` | Beam size for end positions for each start. Total end candidates are `start_n_top * end_n_top`. |
| `--target_eval_key` | `best_f1` | Declared by the CLI; wrappers may use it. The script itself logs all metrics returned by threshold search. |

## Recipe defaults preserved by the builder

| Mode | Key defaults |
| --- | --- |
| `prepro` | `--use_tpu=False`, `--do_prepro=True`, `--max_seq_length=512`, `--max_query_length=64`, `--doc_stride=128`, `--uncased=False`. |
| `gpu-base` | `--use_tpu=False`, `--num_core_per_host=3`, `--train_batch_size=8`, `--predict_batch_size=32`, `--learning_rate=2e-5`, `--train_steps=12000`, `--warmup_steps=1000`, `--save_steps=1000`. |
| `tpu-large` | `--use_tpu=True`, `--num_core_per_host=8`, `--train_batch_size=48`, `--predict_batch_size=32`, `--learning_rate=3e-5`, `--train_steps=8000`, `--warmup_steps=1000`, `--save_steps=1000`. |
| `predict-only` | `--do_train=False`, `--do_predict=True`, `--predict_batch_size=32`, `--n_best_size=5`, `--start_n_top=5`, `--end_n_top=5`. |
