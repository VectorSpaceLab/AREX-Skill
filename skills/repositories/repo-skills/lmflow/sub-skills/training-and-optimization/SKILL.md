---
name: training-and-optimization
description: "Helps build LMFlow fine-tuning and optimization commands for full
  training, LoRA, QLoRA, LISA, and custom optimizers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Optimization

Use this sub-skill when the task is to fine-tune or continue training an LMFlow model, choose an optimizer variant, or prepare a safe command for a training run.

## Typical Triggers

- `finetune`, `train`, `LoRA`, `QLoRA`, `LISA`
- `custom optimizer`, `customized_optim`, `adamw_schedule_free`, `sgdp`, `adabelief`
- `accelerate`, `deepspeed`, `FSDP`, `wandb`
- `output_dir`, `overwrite_output_dir`, `resume_from_checkpoint`

## What This Sub-Skill Owns

- Full fine-tuning and parameter-efficient fine-tuning command construction.
- Custom optimizer name selection and common optimizer arguments.
- Safe output/checkpoint choices and W&B reporting choices.
- The command builder that prints a self-contained LMFlow training snippet.

## Read These First

- `references/workflows.md` for the training variants and their required inputs.
- `references/cli-reference.md` for the key training dataclass fields.
- `references/optimization-reference.md` for the optimizer names and when to use them.
- `references/troubleshooting.md` for OOM, output-path, W&B, and optional dependency issues.
- `scripts/build_finetune_command.py` to render a copyable training command.

## Cross-Links

- Dataset and conversation-template details live in `../data-and-templates/SKILL.md`.
- Non-training generation and evaluation live in `../inference-and-evaluation/SKILL.md`.
- Reward-model, DPO, RAFT, and LoRA-merge flows live in `../post-training-alignment/SKILL.md`.

## Workflow

1. Confirm the model, dataset, and output directory.
2. Choose the method: full, LoRA, QLoRA, LISA, or custom optimizer.
3. Decide whether W&B is enabled or explicitly disabled.
4. Check the dataset template and block-size settings.
5. Render the command with the builder script before a long run.

## Common Decisions

- Use full training when the user wants the simplest baseline and memory is sufficient.
- Use LoRA for most parameter-efficient adaptation tasks.
- Use QLoRA when memory is tight and bitsandbytes is available.
- Use LISA when the user explicitly wants the memory-efficient layer-activation strategy.
- Use a custom optimizer only when the user already knows which optimizer variant they need.

## What Not To Do

- Do not assume the command should run with the current checkout's shell scripts.
- Do not mix vLLM or SGLang concerns into this sub-skill.
- Do not hide output-overwrite or checkpoint-resume decisions.
- Do not claim a GPU workflow is validated just because a CPU import worked.
