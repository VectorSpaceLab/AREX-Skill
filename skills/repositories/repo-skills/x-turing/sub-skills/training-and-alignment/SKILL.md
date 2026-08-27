---
name: training-and-alignment
description: "Fine-tune and align xTuring causal models with supervised
  training, LoRA/quantized variants, and DPO."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Alignment

Use this sub-skill for xTuring model adaptation work:
- supervised fine-tuning via `model.finetune(...)`
- preference alignment via `model.dpo_finetune(...)`
- choosing between full, LoRA, int8, and k-bit training variants
- tuning finetuning config, optimizer, DeepSpeed, and output settings

## Route by task

- For standard text or instruction SFT, start with [finetuning workflows](references/finetuning-workflows.md).
- For preference data and DPO, use [DPO workflow](references/dpo-workflow.md).
- For schema errors, quantization limits, DeepSpeed, and optimizer failures, use [troubleshooting](references/troubleshooting.md).
- For a safe local input check that does not launch training, run [scripts/check_finetuning_inputs.py](scripts/check_finetuning_inputs.py).

If the task is only about model loading, registry inspection, or generation settings, route to the inference-focused skill instead.
