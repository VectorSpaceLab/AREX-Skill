---
name: checkpoint-export
description: "Guides Huatuo-Llama-Med-Chinese LoRA adapter checkpoint export
  into Hugging Face and original LLaMA layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# checkpoint-export

Use this sub-skill when the task is to merge a Huatuo-Llama-Med-Chinese LoRA adapter with its base model and export the result as either a Hugging Face checkpoint or an original LLaMA-style state-dict checkpoint.

## Read first

- [references/workflows.md](references/workflows.md) for supported export modes, required inputs, adapter assumptions, output layouts, and the LLaMA-7B state-dict mapping.
- [references/troubleshooting.md](references/troubleshooting.md) for `BASE_MODEL` assertion failures, hard-coded adapter defaults, missing local files, architecture mismatches, memory/storage pressure, and PEFT/Transformers compatibility issues.
- [scripts/build_export_command.py](scripts/build_export_command.py) to build a dry-run, self-contained export command template without importing Torch or Transformers in the helper itself.

## Route here

Route here for:

- LoRA adapter merge/export planning.
- Building a safe dry-run command for Hugging Face `hf_ckpt/` output.
- Building a safe dry-run command for original LLaMA `ckpt/` output.
- Explaining why state-dict export is limited to LLaMA-7B-compatible models.

## Route elsewhere

- Training or re-training LoRA adapters belongs to `finetuning`.
- Running inference from an unmerged adapter belongs to `inference`.
- Prompt templates, instruction data, and adapter training data formats belong to `prompt-data-formats`.

## Minimal operating checklist

1. Confirm the base model is a local path or Hugging Face model id compatible with the adapter.
2. Confirm the adapter path or Hugging Face adapter id points to a PEFT LoRA adapter directory with `adapter_config.json` and `adapter_model.bin`.
3. Use Hugging Face export unless the downstream consumer explicitly requires the original LLaMA `consolidated.00.pth` plus `params.json` layout.
4. Use state-dict export only for LLaMA-7B-compatible checkpoints; do not apply it to Bloom, Huozi, ChatGLM, or other architectures.
5. Build the dry-run command with the bundled helper, review the emitted warnings, then execute only in an environment with compatible `torch`, `transformers`, `peft`, and enough RAM/storage.
