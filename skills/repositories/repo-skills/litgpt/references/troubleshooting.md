# Cross-Cutting Troubleshooting

Use this reference when a LitGPT task spans multiple sub-skills or fails before the workflow-specific route is clear.

## Install And Import Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: litgpt` | Package not installed in the active Python | Install `litgpt` or the local package, then run `python scripts/check_litgpt_environment.py`. |
| `requests package is required by _set_config_read_mode` | `jsonargparse` URL config mode needs `requests` for CLI startup | Install `requests` or use a complete LitGPT install. |
| Optional logger import fails | Logger choice such as `wandb`, `mlflow`, `tensorboard`, or `litlogger` is not installed | Use `--logger_name csv` for a safe baseline or install the selected logger package. |
| `bitsandbytes` import or quantization failure | `bnb.*` mode requires compatible optional package, CUDA/Linux support, and matching backend | Remove `--quantize` or install/verify `bitsandbytes` in the target runtime. |
| `lm_eval` or `litserve` missing | Evaluation and serving are optional extras | Use `sub-skills/evaluation-serving/scripts/check_optional_eval_serve_deps.py` and install only the needed optional package. |

## Checkpoint And Path Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `checkpoint_dir` does not exist | User passed a Hub model id, typo, or wrong working directory | Route to `sub-skills/checkpoint-conversion/`; download or provide a local path. |
| Missing `lit_model.pth` | HF-format checkpoint, LoRA-only output, partial download, or unmerged training output | Run `sub-skills/checkpoint-conversion/scripts/check_checkpoint_layout.py`; convert, validate, or merge as appropriate. |
| Missing `model_config.yaml` | Directory is not LitGPT format or config files were not copied | Convert/download again or repair config via `checkpoint-conversion`. |
| Missing tokenizer files | Tokenizer was not downloaded or copied beside weights | Download tokenizer files or pass an explicit tokenizer directory where the workflow supports it. |
| LoRA merge fails on `hyperparameters.yaml` | LoRA output metadata is absent or moved | Run `sub-skills/checkpoint-conversion/scripts/check_lora_metadata.py`; recover metadata or pass `--pretrained_checkpoint_dir`. |

## CLI And Config Failures

- Use `litgpt <command> --help` before copying examples between commands; LitGPT uses `jsonargparse` nested flags such as `--train.micro_batch_size` and `--data.json_path`.
- Use `--print_config` for command planning when available. It captures defaults without starting the full workflow.
- Do not mix LoRA-only flags with `finetune_full`; remove `--quantize` when converting QLoRA intent to full finetuning.
- Do not combine `pretrain --resume` with `--initial_checkpoint_dir`; choose resumed run or continued pretraining, not both.
- Use `--resume auto` rather than `--resume true` when an interrupted checkpoint may or may not exist.

## Data And Training Failures

- For JSON/JSONL SFT, every record needs `instruction` and `output`; `input` is optional.
- A single JSON/JSONL file can be split with `--data.val_split_fraction`; a split directory must contain `train.json`/`val.json` or `train.jsonl`/`val.jsonl` and should not set `val_split_fraction`.
- Run `sub-skills/training-data/scripts/validate_json_sft_data.py` before training on custom SFT data.
- Start memory-sensitive training with `--train.micro_batch_size 1`, small `--train.max_seq_length`, a small model, and CSV logging.
- Treat real training and pretraining as user-approved expensive work because they can download checkpoints/data, allocate GPU memory, and run for a long time.

## Hardware And Backend Failures

- CPU-only environments can inspect LitGPT APIs and run static checks, but model loading/generation/training may be slow or impossible for large checkpoints.
- CUDA availability in one Python environment does not prove CUDA availability in another. Verify in the actual runtime that will load weights.
- Tensor-parallel and sequential generation routes require compatible devices and checkpoint size; do not infer success from CLI help alone.
- Thunder and XLA extensions are optional/backend-specific. Do not install or assume them unless the user explicitly requests those workflows.

## Evaluation And Serving Failures

- `litgpt evaluate` with `tasks=None` lists tasks; real tasks require `lm_eval` and may download/compute. Use `--limit` for a bounded smoke run.
- `batch_size` must be a positive integer, `auto`, or `auto:N`.
- `litgpt serve` starts a long-running process and loads checkpoint weights. Check `litserve`, `jinja2`, port availability, and checkpoint layout first.
- Simple `/predict` payloads and OpenAI-compatible `/v1/chat/completions` payloads are different. Use `sub-skills/evaluation-serving/scripts/build_curl_examples.py` to build the correct request shape.

## When To Stop And Ask

Ask before running commands that download model weights, convert large checkpoints, train/pretrain, merge large LoRA weights, evaluate benchmarks, start servers, require credentials, or mutate user-provided environments. Use bundled static checkers and help commands first.
