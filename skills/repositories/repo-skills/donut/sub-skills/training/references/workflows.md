# Workflows

## Core API surface

The training workflow relies on these public objects from the Donut package:

- `DonutDataset(dataset_name_or_path, donut_model, max_length, split='train', ignore_id=-100, task_start_token='<s>', prompt_end_token=None, sort_json_key=True)`
- `JSONParseEvaluator()`
- `DonutModelPLModule(config)`
- `DonutDataPLModule(config)`

See the root API reference in the generated skill tree for the full package summary. The notes below focus on the training and evaluation behavior that matters for this sub-skill.

## Training flow

The bundled `scripts/train_donut.py` is a self-contained copy/adaptation of the official trainer entry point. The explicit CLI flags are only `--config` and `--exp_version`; every other override on the command line is forwarded into the loaded `sconf.Config` object.

A typical run loads a YAML config, merges overrides, derives `exp_name` from the config filename, and writes the effective config to `result_path/exp_name/exp_version/config.yaml` before fitting starts. The main training artifacts live under the same `result_path/exp_name/exp_version/` directory.

Example from this sub-skill directory:

```bash
python scripts/check_training_config.py --config references/configs/train_cord.yaml
python scripts/train_donut.py --config references/configs/train_cord.yaml \
  --pretrained_model_name_or_path naver-clova-ix/donut-base \
  --dataset_name_or_paths '["naver-clova-ix/cord-v2"]' \
  --exp_version smoke
```

The Lightning module behavior is important when explaining run dynamics:

- `DonutModelPLModule.training_step` concatenates the per-dataset batch tensors, applies teacher forcing, and logs `train_loss`.
- `DonutModelPLModule.validation_step` slices the decoder prompt up to the prompt end token, runs `model.inference(return_json=False)`, strips prompt tags and EOS markers, and computes normalized edit distance per sample.
- `DonutModelPLModule.on_validation_epoch_end` logs `val_metric_{i}th_dataset` for each loader and one aggregate `val_metric` across all validation loaders.
- `DonutModelPLModule.configure_optimizers` requires either `max_epochs` or `max_steps`. If `max_epochs > 0`, the source code asserts that only one dataset is configured.
- `DonutModelPLModule.on_save_checkpoint` saves the pretrained model and tokenizer into the run directory, so the checkpoint root is also the export root.
- `DonutDataPLModule` builds one train and one validation dataloader per dataset and seeds each worker deterministically.

Important consequences:

- If you want multi-dataset training, prefer `max_steps` over `max_epochs`.
- If you use `max_epochs`, keep `dataset_name_or_paths` to a single dataset.
- Keep `dataset_name_or_paths`, `train_batch_sizes`, `val_batch_sizes`, and optional `task_start_tokens` aligned by index.
- A clean run directory usually contains `config.yaml`, `artifacts.ckpt`, `pytorch_model.bin`, tokenizer files, and logger output.

## Evaluation flow

The bundled `scripts/evaluate_dataset.py` mirrors the source evaluation script. Its explicit CLI flags are:

- `--pretrained_model_name_or_path`
- `--dataset_name_or_path`
- `--split` (default `test`)
- `--task_name` (defaults to the basename of the dataset path or hub id)
- `--save_path`

The script loads the dataset, builds a prompt from the task name, and then scores each sample:

- `docvqa`: the prompt uses the first question from `gt_parses`, lowercased, with `<s_answer>` as the prompt end token. The source script scores exact answer match.
- `rvlcdip`: the source script scores exact class match.
- all other tasks: the source script uses `JSONParseEvaluator.cal_acc` for normalized tree-edit-distance accuracy.

The same helper can also validate local `metadata.jsonl` files before a checkpoint is loaded.

## Resume flow

The source config key is `resume_from_checkpoint_path`.

- Use the run directory created by training, not the top-level `result_path`.
- The resume path must have the checkpoint file and the saved model files expected by `CustomCheckpointIO`.
- If you change `input_size`, `max_length`, or the pretrained backbone, treat the checkpoint as potentially incompatible until you verify the new shapes.

## Metric interpretation

| Metric | Source | Better | Meaning |
| --- | --- | --- | --- |
| `train_loss` | `training_step` | lower | teacher-forced decoder loss |
| `val_metric` | `on_validation_epoch_end` | lower | mean normalized edit distance across validation loaders |
| `val_metric_{i}th_dataset` | per-loader validation | lower | dataset-specific normalized edit distance |
| `TED accuracy` / `ted_accuracy` | evaluation helper | higher | normalized tree-edit-distance accuracy |
| `F1 accuracy` / `f1_accuracy` | `JSONParseEvaluator.cal_f1` | higher | micro-averaged field-level F1 |

Do not compare `val_metric` and `ted_accuracy` without remembering that one is an error-like quantity and the other is an accuracy-like quantity.

## Cross-link reminders

- For prompt-level generation details and `return_json` behavior, use the inference sub-skill.
- For synthetic dataset generation, use the SynthDoG sub-skill.
