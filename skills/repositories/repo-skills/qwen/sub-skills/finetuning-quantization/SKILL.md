---
name: finetuning-quantization
description: "Route Qwen SFT, LoRA, Q-LoRA, DeepSpeed, adapter merge, and GPTQ
  quantization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen Fine-Tuning and Quantization

Use this sub-skill when the user wants to prepare supervised fine-tuning data, run full-parameter fine-tuning, LoRA, Q-LoRA, merge adapters, or quantize a fine-tuned Qwen checkpoint with GPTQ.

## Safe start

- Use `scripts/validate_finetune_data.py` to validate the JSON training data shape before launching training.
- Use `scripts/build_finetune_command.py` to print a command plan without starting training or loading a model.
- Treat GPU, DeepSpeed, PEFT, and AutoGPTQ requirements as explicit prerequisites, not as implied by a Transformers import.

## Routes

| User request | Read |
| --- | --- |
| Training data shape, `finetune.py` arguments, masking, dataset loading, or file format issues | `references/data-format.md` |
| Full fine-tuning, LoRA, Q-LoRA, DeepSpeed, FSDP, multinode, and merge/save behavior | `references/finetuning-workflows.md` |
| GPTQ quantization, output conversion, model copy steps, or AutoGPTQ compatibility | `references/quantization.md` |
| GPU memory, ZeRO stages, precision, optional deps, checkpoint naming, or training failure modes | `references/deepspeed-and-hardware.md` |
| Validation, optional dependency, adapter, GPTQ, or data-format errors | `references/troubleshooting.md` |

## Boundaries

- For ordinary inference of the resulting checkpoint, use `../inference-model-loading/SKILL.md`.
- For serving the fine-tuned model, use `../serving-deployment/SKILL.md`.
- For function-calling training samples or ChatML/tokenizer details, use `../prompting-tool-use-tokenization/SKILL.md`.
- For evaluation scripts, use `../evaluation-reproduction/SKILL.md`.

## Operating rules

- Keep data validation separate from training. A valid JSON sample does not prove that training will fit in memory or that the chosen ZeRO stage is compatible.
- For Q-LoRA, the repository expects the Int4 chat checkpoint and fp16, not a BF16 base checkpoint.
- Do not recommend merging Q-LoRA adapters into a standalone model; that path is only documented for LoRA.
- Do not run `torchrun`, `deepspeed`, GPTQ quantization, or adapter merge as a smoke test unless the user explicitly wants the side effect.
