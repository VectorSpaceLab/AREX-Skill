---
name: training-data
description: "Plan and validate LitGPT finetuning, LoRA/QLoRA/full/adapter
  training, pretraining, data modules, JSON/JSONL SFT data, recipes, TrainArgs,
  EvalArgs, LogArgs, and OOM-safe training commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LitGPT Training And Data

Use this sub-skill when the task is about supervised finetuning, LoRA or QLoRA, full finetuning, adapter or adapter_v2 finetuning, pretraining or continued pretraining, LitGPT data modules, JSON/JSONL SFT data, training recipes, logging, resume, evaluation during training, or training-command risk checks.

Route elsewhere:

- Use `../inference-chat/` for generation or chat after training.
- Use `../checkpoint-conversion/` for checkpoint download, validation, conversion, and LoRA merge.
- Use `../evaluation-serving/` for LM Evaluation Harness runs and serving APIs.

## Fast Workflow

1. Pick the training family: `finetune_lora`/QLoRA for parameter-efficient SFT, `finetune_full` for all-parameter SFT, `finetune_adapter` or `finetune_adapter_v2` for adapter SFT, and `pretrain` for scratch or continued language-model pretraining.
2. Validate the base checkpoint or model selection before training; finetuning commands require a base `checkpoint_dir`, while `pretrain` requires a `model_name` and usually a tokenizer/data plan.
3. Validate the data source with `scripts/validate_json_sft_data.py` for JSON/JSONL SFT data or with `litgpt <command> --data.help <DataModule>` for built-in modules.
4. Start from a bundled YAML recipe or a minimal CLI command, then summarize risks with `scripts/summarize_training_command.py` before running anything expensive.
5. Reduce OOM risk first with `--train.micro_batch_size 1`, `--train.max_seq_length`, lower precision, smaller model/recipe, or a parameter-efficient method.

## Required References

- `references/cli-reference.md` covers supported commands, core options, and argument incompatibilities.
- `references/data-formats.md` covers JSON/JSONL SFT data, directory splits, and built-in data modules.
- `references/config-recipes.md` covers config hub recipe patterns and safe recipe adaptation.
- `references/workflows.md` covers finetuning, QLoRA-to-full conversion, pretraining, resume, logging, and validation workflows.
- `references/troubleshooting.md` covers data, command, quantization, logger, resume, OOM, download, and dependency failures.

## Safe Helper Scripts

- `scripts/validate_json_sft_data.py` validates JSON/JSONL SFT files or split directories without loading a tokenizer or starting training.
- `scripts/summarize_training_command.py` inspects an intended `litgpt finetune*` or `litgpt pretrain` command and flags likely incompatible, missing, or OOM-prone choices.

Both scripts are deterministic and local-only. They do not download data, load models, start training, mutate checkpoints, start servers, or require credentials.

## Source Evidence

This guidance is distilled from LitGPT CLI help, training/data source contracts, data tests, finetune/pretrain tutorials, OOM guidance, config hub recipes, and installed API signature checks. It is self-contained; do not depend on the original repository checkout at runtime.
