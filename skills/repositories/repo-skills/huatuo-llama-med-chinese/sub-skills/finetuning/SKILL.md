---
name: finetuning
description: "Guides LoRA instruction fine-tuning for Huatuo-Llama-Med-Chinese
  style medical QA data using PEFT and Transformers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Finetuning

Use this sub-skill when the task is to plan, validate, or construct a safe dry-run command for LoRA instruction fine-tuning on Chinese medical QA data with the repository-compatible PEFT/Transformers training interface.

## Route here for

- LoRA fine-tuning parameter selection: batch size, micro batch size, epochs, learning rate, cutoff length, validation size, and LoRA rank/alpha/dropout/target modules.
- Medical QA training data checks for the required JSONL fields `instruction`, `input`, and `output`.
- W&B, DDP, checkpoint resume, and adapter save behavior for the training workflow.
- Safe command construction with the bundled dry-run builder: [`scripts/build_finetune_command.py`](scripts/build_finetune_command.py).

## Route elsewhere

- Prompt template JSON semantics, `Prompter` behavior, or data conversion details: use `prompt-data-formats`.
- Merging or exporting LoRA adapters after training: use `checkpoint-export`.
- Running inference from a trained adapter: use `inference`.

## Required reading in this sub-skill

- Workflow and resource guidance: [`references/workflows.md`](references/workflows.md).
- Training interface and defaults: [`references/api-reference.md`](references/api-reference.md).
- Failure diagnosis: [`references/troubleshooting.md`](references/troubleshooting.md).
- Dry-run command builder: [`scripts/build_finetune_command.py`](scripts/build_finetune_command.py).

## Minimal safe workflow

1. Validate that every training record is JSONL with string fields `instruction`, `input`, and `output`; `input` may be an empty string but should still be present for this training implementation.
2. Choose a prompt template name. For the medical-knowledge LLaMA/Alpaca workflow, use `med_template` unless a different compatible template is intentional.
3. Build a dry-run command with the bundled builder. Do not start training until model assets, CUDA/bitsandbytes compatibility, output storage, and W&B/DDP behavior are reviewed.
4. For limited memory GPUs, lower `micro_batch_size`, lower total `batch_size`, and consider lowering `cutoff_len` before attempting training.
5. When resuming, point `resume_from_checkpoint` at either a Trainer checkpoint directory or a LoRA adapter directory whose LoRA configuration matches the new run.

## Safety notes

Full fine-tuning is expensive and depends on external base-model weights, GPU memory, a compatible Torch/CUDA/bitsandbytes stack, and medical-data quality. The bundled script only builds and optionally validates a command; it does not import model libraries, download weights, or launch training.
