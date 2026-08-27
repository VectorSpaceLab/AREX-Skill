# Training Workflows and Command Patterns

## When to read

Read this when choosing pretraining, full fine-tuning, LoRA, QLoRA, or task-specific LLaVA command templates.

## High-level workflow order

1. Prepare or validate the dataset JSON.
2. Choose the training mode.
3. Select the DeepSpeed config.
4. Set the model path, version, vision tower, image folder, and output directory.
5. Add LoRA or projector flags only when the workflow requires them.
6. Launch the command and monitor GPU memory, checkpoint writes, and W&B logging.

## Common templates

### Projector pretraining

Use when learning a multimodal projector from image-text pairs.

Key flags:
- `--tune_mm_mlp_adapter True`
- `--vision_tower openai/clip-vit-large-patch14` or `...-336` depending on the checkpoint family
- `--mm_vision_select_layer -2`
- `--mm_use_im_start_end False`
- `--mm_use_im_patch_token False`

### Full instruction fine-tuning

Use when you already have a projector and want to train the full model or the main multimodal adaptation path.

Key flags:
- `--pretrain_mm_mlp_adapter <projector.bin>` when required by the workflow
- `--mm_projector_type mlp2x_gelu` for v1.5-style scripts
- `--group_by_modality_length True` when the script expects it

### LoRA / QLoRA

Use when the user wants a parameter-efficient tune or reduced memory footprint.

Key flags:
- `--lora_enable True`
- `--lora_r <rank>`
- `--lora_alpha <alpha>`
- `--bits 4` for the QLoRA-style script
- `--mm_projector_lr` for projector-specific learning rate tuning

## DeepSpeed config choice

| Config | Typical use | Tradeoff |
| --- | --- | --- |
| `zero2.json` | simpler pretraining or projector-only work | lighter than ZeRO-3 but less memory efficient |
| `zero3.json` | default for large instruction fine-tuning | better memory efficiency on multi-GPU hosts |
| `zero3_offload.json` | when GPU memory is tight | offloads optimizer/params to CPU, usually slower |

## Verified script patterns distilled from the repo

- `scripts/v1_5/pretrain.sh` uses `llava/train/train_mem.py`, `--deepspeed ./scripts/zero2.json`, a Vicuna base model, a `plain` prompt version, a pretraining data file, and `--tune_mm_mlp_adapter True`.
- `scripts/v1_5/finetune.sh` uses `--deepspeed ./scripts/zero3.json`, `--pretrain_mm_mlp_adapter`, and a v1 prompt version.
- `scripts/v1_5/finetune_lora.sh` uses `--lora_enable True`, `--lora_r 128`, `--lora_alpha 256`, and `--mm_projector_lr 2e-5`.
- `scripts/v1_5/finetune_task_lora.sh` and `scripts/v1_5/finetune_task.sh` show the task-specific fine-tune shape.
- `scripts/v1_5/finetune_sqa.sh` shows the ScienceQA training pattern.

## When to prefer parameter-efficient tuning

Prefer LoRA or QLoRA when the user wants to:

- reduce memory pressure
- keep the base model frozen or mostly frozen
- adapt a checkpoint to a narrow domain with limited compute

Prefer full fine-tuning when the user has enough GPU memory and wants to adjust the full model behavior.

## Safety notes

- A CPU import check is not evidence that training will work.
- A GPU with CUDA is necessary but may still be insufficient if the checkpoint or batch size is too large.
- We do not run full training inside this skill; we only build and validate commands and data layout.
