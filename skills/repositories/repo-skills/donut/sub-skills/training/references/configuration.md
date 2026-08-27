# Configuration

## Dataset JSONL contract

Donut training and evaluation expect split folders laid out like this:

```text
dataset_root/
  train/
    metadata.jsonl
    *.png|*.jpg|*.jpeg
  validation/
    metadata.jsonl
    *.png|*.jpg|*.jpeg
  test/
    metadata.jsonl
    *.png|*.jpg|*.jpeg
```

Each line in `metadata.jsonl` is a JSON object with at least these fields:

- `file_name`: relative path to the image file for that split
- `ground_truth`: a JSON-encoded string, not a nested object

Extra metadata keys may be present, but the training and evaluation code ignores them.

### Single-answer examples

```json
{"file_name": "0001.png", "ground_truth": "{\"gt_parse\": {\"class\": \"scientific_report\"}}"}
{"file_name": "0042.png", "ground_truth": "{\"gt_parse\": {\"menu\": [{\"nm\": \"ICE BLACKCOFFEE\", \"cnt\": \"2\"}]}}"}
```

For single-answer tasks, `ground_truth` must decode to an object containing `gt_parse`, and `gt_parse` must be a dictionary.

### Multi-answer example

```json
{"file_name": "test/0007.png", "ground_truth": "{\"gt_parses\": [{\"question\": \"what is the model name?\", \"answer\": \"donut\"}, {\"question\": \"what is the model name?\", \"answer\": \"document understanding transformer\"}]}"}
```

For DocVQA-style tasks, `ground_truth` must decode to an object containing `gt_parses`, and `gt_parses` must be a list of dictionaries.

`DonutDataset` behaves like this:

- train split: randomly chooses one target from `gt_parses` when multiple answers exist
- validation split: returns the prompt end index and the raw processed parse string
- `task_start_token` and `prompt_end_token` are added to the decoder tokenizer before tokenization

## CLI reference

### Training

The bundled `scripts/train_donut.py` has only two explicit argparse flags:

- `--config` (required): YAML config file path
- `--exp_version` (optional): overrides the run subdirectory; otherwise the trainer uses a timestamp

Everything else is passed through to `sconf.Config.argv_update(left_argv)`. That means you can override YAML keys on the command line, for example:

```bash
python scripts/train_donut.py --config references/configs/train_cord.yaml \
  --pretrained_model_name_or_path naver-clova-ix/donut-base \
  --dataset_name_or_paths '["naver-clova-ix/cord-v2"]' \
  --exp_version smoke
```

### Evaluation

The bundled `scripts/evaluate_dataset.py` exposes these explicit flags:

- `--pretrained_model_name_or_path`
- `--dataset_name_or_path`
- `--split` (default `test`)
- `--task_name` (default: basename of the dataset path or hub id)
- `--save_path`

## Task-specific config examples

The values below are distilled from the bundled YAML examples in `references/configs/`.

| Task | Dataset source | input_size | max_length | train_batch_sizes | val_batch_sizes | sort_json_key | lr | warmup_steps | num_training_samples_per_epoch | max_epochs | gradient_clip_val | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CORD | hub dataset | `[1280, 960]` | `768` | `[8]` | `[1]` | `False` | `3e-5` | `300` | `800` | `30` | `1.0` | README notes a single A100 run; preprocessed CORD keeps key order as-is |
| DocVQA | local `docvqa` dataset | `[2560, 1920]` | `128` | `[2]` | `[4]` | `True` | `3e-5` | `10000` | `39463` | `300` | `0.25` | source comments mention a larger multi-node training setup |
| RVL-CDIP | local `rvlcdip` dataset | `[2560, 1920]` | `8` | `[2]` | `[4]` | `True` | `2e-5` | `10000` | `320000` | `100` | `1.0` | task-specific class tokens are added automatically |
| ZH TrainTicket | local `zhtrainticket` dataset | `[960, 1280]` | `256` | `[8]` | `[1]` | `True` | `3e-5` | `300` | `1368` | `10` | `1.0` | `max_length` is longer because the label space is more verbose |

Common config fields used across the source examples:

- `result_path`: output root, default `./result`
- `resume_from_checkpoint_path`: checkpoint root for resume, default `null`
- `pretrained_model_name_or_path`: hub id or local checkpoint directory
- `dataset_name_or_paths`: list of dataset names or local paths
- `num_nodes`: source examples use `1`; some comments show larger multi-node settings for published checkpoints
- `seed`: source examples use `2022`
- `align_long_axis`: source examples use `False`
- `val_check_interval`: source examples use `1.0`
- `check_val_every_n_epoch`: task-dependent validation cadence
- `verbose`: prints one prediction/answer pair during validation when `True`

## Config constraints to keep in mind

- `dataset_name_or_paths`, `train_batch_sizes`, and `val_batch_sizes` must have the same length.
- If `task_start_tokens` is present, it must also match that length.
- If `max_epochs > 0`, the source code asserts that only one dataset is configured.
- If you need multiple datasets, use `max_steps` rather than `max_epochs`.
- For DocVQA, the source trainer uses `<s_answer>` as the prompt end token.
- For non-DocVQA tasks, the prompt end token defaults to the task token, such as `<s_cord-v2>` or `<s_rvlcdip>`.
- The helper script `scripts/check_training_config.py` enforces the list-length and epoch constraints and can inspect local metadata files.
