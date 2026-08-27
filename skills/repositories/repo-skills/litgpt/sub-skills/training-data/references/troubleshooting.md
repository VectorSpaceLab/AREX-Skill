# Training Troubleshooting

Use this checklist before launching or when triaging LitGPT training failures.

## JSON/JSONL Data Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `json_path ... does not exist` | Data path typo or missing mount/download | Use an existing file or split directory; validate with `scripts/validate_json_sft_data.py`. |
| `Unsupported file format` | File suffix is not `.json` or `.jsonl` | Rename/convert to JSON list or JSONL records. |
| Directory requires train and val | Directory lacks `train.json`/`val.json` or `.jsonl` equivalents | Add both split files or pass a single file with `val_split_fraction`. |
| `val_split_fraction should not be set` | A split directory was combined with a random split fraction | Remove `--data.val_split_fraction` for directories. |
| Defaulting to `val_split_fraction=0.05` | Single file without explicit split fraction | Set `--data.val_split_fraction` explicitly to the intended value. |
| KeyError for `instruction` or `output` | One or more records missing required SFT keys | Fix rows; `input` is optional but often useful as `""`. |
| JSON decode error in JSONL | Malformed line or trailing partial record | Fix the reported line; validate with row-level diagnostics. |

## Command And Argument Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing `checkpoint_dir` | Finetuning command lacks required positional checkpoint | Add a local checkpoint path or model name and validate/download first. |
| Missing `model_name` | `pretrain` lacks required positional model name | Add a supported model name or config-backed recipe. |
| Finetune rejects `max_tokens`, `max_norm`, `tie_embeddings`, or `lr_warmup_fraction` | Pretrain-only or unsupported TrainArgs passed to finetuning | Remove them; use `epochs`, `max_steps` for debug, and supported finetune fields. |
| Pretrain rejects `epochs` or `eval.max_new_tokens` | Finetune-only args passed to pretrain | Remove them; use `max_tokens`/`max_time` and validation loss settings. |
| Pretrain requires `max_tokens` or `max_norm` | Required pretrain TrainArgs omitted | Add `--train.max_tokens <n>` and `--train.max_norm <float>`. |
| `lr_warmup_fraction` conflict | Both warmup fraction and steps were set | Keep only one; fraction must be in `[0, 1]`. |
| `global_batch_size` assertion | Batch too small for devices/nodes/micro batch | Increase global batch or reduce devices/nodes/micro batch. |

Run the command summarizer for preflight warnings:

```bash
python scripts/summarize_training_command.py -- litgpt pretrain pythia-14m --data TextFiles --data.train_data_path data/text
```

## Quantization And Precision

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Quantization and mixed precision is not supported` | `--quantize` combined with `bf16-mixed` or `16-mixed` | Use `bf16-true`, `16-true`, or `32-true`. |
| Quantized multi-GPU not supported | `--quantize` with `--devices > 1` or `--num_nodes > 1` | Use one device/node or remove quantization. |
| Full finetuning rejects `--quantize` | Full command has no quantization option | Use `finetune_lora` for QLoRA or remove quantization for full finetuning. |
| bitsandbytes import/runtime failure | Optional dependency missing or incompatible | Install compatible bitsandbytes for the target CUDA/Python stack or use non-quantized training. |

## OOM And Hardware

OOM usually means the model, context length, batch size, optimizer, and precision exceed available accelerator memory.

Try in order:

1. Set `--train.micro_batch_size 1`.
2. Set `--train.max_seq_length 256` or `512` for SFT; reduce pretrain block/model config length where appropriate.
3. Use LoRA/adapter instead of full finetuning.
4. Use lower true precision if supported, such as `bf16-true`; avoid mixed precision with quantization.
5. Use a smaller model or smaller recipe.
6. For non-quantized full/adapter training, consider multiple GPUs/devices with the strategy LitGPT selects.
7. Use a lighter optimizer only with a deliberate training-quality trade-off.

Do not raise `global_batch_size`, `micro_batch_size`, sequence length, and model size at the same time; scale one dimension per run.

## Resume Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Resume path missing | Explicit `--resume <path>` is wrong | Point to an existing LitGPT step checkpoint directory/file. |
| `--resume true` errors when no checkpoint exists | Strict resume expected a previous checkpoint | Use `--resume auto` for reusable commands or start without resume. |
| Pretrain rejects resume with initial checkpoint | Both `--resume` and `--initial_checkpoint_dir` set | Choose resume for interrupted same run, initial checkpoint for continued pretraining. |
| Adapter v2 resume finds no adapter checkpoint | `out_dir` lacks `step-*/*.pth.adapter_v2` | Start fresh or provide the correct out_dir/checkpoint history. |

## Logger And Optional Dependencies

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| TensorBoard/WandB/MLflow/LitLogger import error | Optional logger dependency missing | Use `--logger_name csv` or install/configure the chosen logger. |
| WandB prompts or auth failures | Remote logger requires credentials | Switch to `csv` for offline/local runs or configure credentials outside recipes. |
| LitData import error | `LitData` data module requires optional `litdata` package | Install optional dependency or use `TextFiles`/prepared local module. |
| Dataset download/access failure | Built-in dataset requires network, optional package, or token | Use local JSON/TextFiles data or provide access token through secure runtime means. |

## Downloads And Tokens

Training commands may trigger downloads when `checkpoint_dir` is a model name or when built-in data modules fetch datasets.

- For reproducible offline runs, download/checkpoint-validate first via the checkpoint sub-skill and use local paths.
- Do not embed access tokens in reusable commands or YAML files.
- If a dataset/model is gated, confirm access before training.

## Output And Checkpoint Confusion

- LoRA output saves adapter weights such as `lit_model.pth.lora`; merge to a full checkpoint via the checkpoint sub-skill.
- Adapter outputs save adapter-specific checkpoint suffixes; use the matching generation/merge/conversion route.
- Full finetuning and pretraining save `final/lit_model.pth` plus config/tokenizer-related files when available.
- Use distinct `out_dir` values per experiment to avoid accidental resume or overwrites.

## Diagnostic Order

1. Validate data paths/schema.
2. Validate checkpoint/model/tokenizer availability.
3. Summarize command risks.
4. Inspect merged config with `--print_config`.
5. Use CSV logging and conservative memory settings.
6. Run a tiny smoke only when hardware/network/dependency prerequisites are confirmed.
7. Route checkpoint merge/conversion, post-training generation, or external evaluation to sibling sub-skills.
