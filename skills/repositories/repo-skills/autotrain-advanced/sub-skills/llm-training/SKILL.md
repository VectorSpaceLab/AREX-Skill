---
name: llm-training
description: "Operate AutoTrain Advanced LLM finetuning workflows, config
  aliases, data columns, PEFT/quantization knobs, and adapter flow."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: autotrain-advanced
license: Apache 2.0
---

# AutoTrain LLM training

Use this sub-skill for `autotrain llm`, LLM YAML configs, app/API LLM task keys, PEFT/LoRA, quantization, unsloth, and adapter-related decisions.

## Supported entry points

- CLI: `autotrain llm --help`
- CLI training: `autotrain llm --train ...`
- YAML config aliases: `llm`, `llm-sft`, `llm-dpo`, `llm-orpo`, `llm-reward`, `llm-generic`
- App/API task keys: `llm:sft`, `llm:dpo`, `llm:orpo`, `llm:reward`, `llm:generic`
- Config examples: `configs/llm_finetuning/*.yml`

Do not suggest `--deploy` or `--inference` as working LLM commands; in this checkout those branches raise `NotImplementedError`.

## Required CLI fields for training

For `autotrain llm --train`, make sure the user provides at least:

- `--project-name`
- `--data-path`
- `--model`

If `--push-to-hub` is used, `--username` and `--token` are required. Hosted backends such as `spaces-*` and `ep-*` also require Hub push credentials.

## Common LLM knobs

- Data: `data_path`, `train_split`, `valid_split`, `text_column`, `prompt_text_column`, `rejected_text_column`, `chat_template`.
- Sequence: `block_size` / `block-size`, `model_max_length`, `max_prompt_length`, `max_completion_length`, `padding`, `add_eos_token`.
- Training: `trainer`, `epochs`, `batch_size`, `gradient_accumulation`, `lr`, `scheduler`, `optimizer`, `mixed_precision`, `auto_find_batch_size`.
- PEFT/LoRA: `peft`, `quantization`, `target_modules`, `lora_r`, `lora_alpha`, `lora_dropout`, `merge_adapter`.
- Preference tuning: `model_ref`, `dpo_beta`, `rejected_text_column`, `prompt_text_column`.
- Acceleration: `use_flash_attention_2`, `unsloth`, `distributed_backend`.

## Safe validation sequence

1. Inspect the command: `python ../../scripts/inspect_cli.py llm --help` from this sub-skill directory's parent skill root, or use the absolute root helper path.
2. Validate a YAML file without launching: `python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/llm.yml`.
3. Validate local CSV/JSONL columns with `../text-and-tabular/scripts/validate_text_data.py --task llm ...` when the dataset is local.
4. Route adapter merging to `../model-tools/` rather than duplicating that logic here.

## References

- `references/workflows.md` — command templates, config aliases, trainers, and field groups.
- `references/troubleshooting.md` — auth, backend, PEFT, quantization, and unsupported deploy/inference recovery.
