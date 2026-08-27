# Qwen-VL finetuning launch reference

This reference condenses the official launch templates into a workflow-oriented map. Replace the placeholder values before running any job.

## Shared placeholders

- `MODEL`: the checkpoint or local model directory.
- `DATA`: the JSON training dataset.
- `OUTPUT_DIR`: the directory that will receive checkpoints and adapter files.
- `GPUS_PER_NODE`, `NNODES`, `NODE_RANK`, `MASTER_ADDR`, `MASTER_PORT`: distributed launch settings.

## Full finetuning

Use the full-parameter template when you want all model weights updated.

- Bundle: `scripts/finetune_full_ds.sh`
- Script: `scripts/finetune.py`
- Deepspeed config: `scripts/ds_config_zero3.json`

Typical intent:

- BF16 on Ampere-or-newer GPUs.
- Freeze the visual encoder if you want the source repo's default behavior.
- Use a large enough output directory because full checkpoints are saved.

## LoRA finetuning

Use LoRA when you want a lighter adapter.

- Bundle: `scripts/finetune_lora_single_gpu.sh`
- Bundle: `scripts/finetune_lora_ds.sh`
- Script: `scripts/finetune.py`
- Deepspeed config: `scripts/ds_config_zero2.json`

Typical intent:

- `--use_lora`
- Usually `--bf16 True`
- The adapter only saves the LoRA layers unless you intentionally request merged standalone weights later.

## Q-LoRA finetuning

Use Q-LoRA when memory pressure is the limiting factor.

- Bundle: `scripts/finetune_qlora_single_gpu.sh`
- Bundle: `scripts/finetune_qlora_ds.sh`
- Script: `scripts/finetune.py`
- Deepspeed config: `scripts/ds_config_zero2.json`

Typical intent:

- `--use_lora`
- `--q_lora`
- `--fp16 True` instead of `--bf16 True`
- Prefer `Qwen/Qwen-VL-Chat-Int4` as the starting point

## Common flags worth knowing

- `--model_name_or_path`: checkpoint or local path.
- `--data_path`: training JSON.
- `--eval_data_path`: optional evaluation JSON.
- `--output_dir`: adapter/checkpoint destination.
- `--model_max_length`: sequence-length budget.
- `--lazy_preprocess`: skip eager preprocessing when the dataset is large.
- `--fix_vit`: freeze the vision tower by default.
- `--gradient_checkpointing`: save memory at the cost of speed.

## After training

- For LoRA adapters, use the inference sub-skill to load `AutoPeftModelForCausalLM` or the equivalent adapter path.
- The source docs say LoRA adapters can be merged into a standalone model, but Q-LoRA adapters cannot be merged in the same way.
- If the user needs benchmark numbers after training, route to the evaluation sub-skill instead of training again.
