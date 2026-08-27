# CLI and API front doors

Use the installed package modules rather than source-checkout paths whenever possible.

| Command or API | Purpose | Read when |
| --- | --- | --- |
| `python -m easycv.tools.train` / `easycv.tools.train(...)` | Train or fine-tune a config-driven model | The task is training, distributed launch, or resume / seed / fp16 setup. |
| `python -m easycv.tools.eval` / `easycv.tools.eval(...)` | Evaluate a checkpoint against a config | The task is checkpoint evaluation, validation metrics, or test-time result export. |
| `python -m easycv.tools.export` / `easycv.tools.export(...)` | Export a checkpoint for inference | The task is to create a raw / JIT / Blade / ONNX-style inference artifact. |
| `python -m easycv.tools.predict` | Run batch prediction over file lists or ODPS tables | The task is large-scale prediction, table I/O, or image URL / base64 ingestion. |
| `python -m easycv.tools.prune` | Run pruning and compression | The task needs pruning-specific compression workflows. |
| `python -m easycv.tools.quantize` | Run quantization | The task needs CPU / backend quantization workflows. |
| `python -m easycv.tools.launch` | Launch distributed jobs | You need the repo's launch wrapper rather than calling `torch.distributed` manually. |

## Python APIs that mirror the CLI wrappers

- `easycv.tools.train(config_path, gpus=1, fp16=False, master_port=29527)`
- `easycv.tools.eval(config_path, checkpoint_path, gpus=1, fp16=False, master_port=29600)`
- `easycv.tools.export(config_path, checkpoint_path, export_path)`

## Common shared arguments

These appear across the training and evaluation tools:

- `--work_dir`
- `--load_from`
- `--resume_from`
- `--fp16`
- `--launcher`
- `--seed`
- `--model_type`
- `--user_config_params`

The prediction front door also uses:

- `--input_file` / `--output_file`
- `--input_table` / `--output_table`
- `--model_path`
- `--model_type`
- `--image_col`
- `--image_type`
- `--reserved_columns`
- `--result_column`
- `--odps_config`

