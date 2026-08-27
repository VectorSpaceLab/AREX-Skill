---
name: model-loading-and-adapters
description: "Guides agents choosing and troubleshooting Axolotl model configs,
  tokenizer or processor loading, LoRA and QLoRA adapters, quantization,
  multimodal models, and architecture quirks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Loading and Adapters

Use this sub-skill when the task is about Axolotl `base_model`, tokenizer or processor loading, `chat_template` mismatches, LoRA/QLoRA target modules, bitsandbytes or torchao quantization, multimodal/VLM config, Gemma/Qwen/Mistral/Llama quirks, attention backend selection, or adding support for a new model architecture.

## Read First

- [references/model-selection.md](references/model-selection.md) for `base_model`, tokenizer, processor, chat template, attention backend, multimodal, and architecture-family choices.
- [references/adapters-and-quantization.md](references/adapters-and-quantization.md) for LoRA, QLoRA, ReLoRA, `lora_target_modules`, `lora_target_parameters`, bitsandbytes, MoE expert quantization, QAT, and PTQ.
- [references/new-model-support.md](references/new-model-support.md) for unsupported architecture debugging, user-agent touchpoints, validation order, and patch/test planning.
- [references/troubleshooting.md](references/troubleshooting.md) for symptom-driven fixes around gated models, tokenizer trust, chat templates, LoRA targets, QLoRA backends, multimodal processors, attention kernels, and new-model failures.
- [scripts/check_model_config.py](scripts/check_model_config.py) for a safe static YAML check before `axolotl preprocess`; it never downloads, loads a model, imports Axolotl, or starts training.

## Quick Workflow

1. Identify the model family and wrapper first: text-only causal LM, multimodal `ForConditionalGeneration`, MoE/hybrid model, pre-quantized checkpoint, or new/remote-code architecture.
2. Set model-loading fields before training-method fields: `base_model`, optional `base_model_config`, `tokenizer_config`, `tokenizer_type`, `processor_type`, `trust_remote_code`, `attn_implementation`, and `chat_template`.
3. Choose adapter and quantization together: full fine-tune has no `adapter`; LoRA usually targets explicit modules; QLoRA requires `adapter: qlora` plus `load_in_4bit: true`; MoE expert LoRA uses `lora_target_parameters` with `lora_dropout: 0`.
4. For multimodal models, include the processor path: usually `processor_type: AutoProcessor`, `skip_prepare_dataset: true`, `remove_unused_columns: false`, `sample_packing: false`, and a model-appropriate `chat_template`.
5. Run `python scripts/check_model_config.py config.yaml` for local structural warnings, then use `axolotl preprocess config.yaml` or `axolotl preprocess config.yaml --debug` in the user's Axolotl environment for real tokenizer/model-schema validation.
6. Only after config and preprocessing are consistent, route method-specific tuning to the SFT, preference, RL, or distributed sibling sub-skills.

## Boundaries

- This sub-skill owns model/tokenizer/processor loading choices, adapter config, quantization fields, architecture-specific notes, multimodal support, attention backend selection, and new-model debugging guidance.
- Route SFT and continual pretraining recipes to `sft-and-pretraining`.
- Route DPO, IPO, KTO, ORPO, SimPO, reward-model, GRPO, and EBFT method recipes to `preference-tuning` or `rl-and-rewards`.
- Route generic dataset formats, column mappings, and YAML schema mechanics to `data-and-configs`.
- Route DeepSpeed, FSDP, launch topology, memory budgets, vLLM serving, and performance tuning to `distributed-and-performance`.
- Route complete CLI operations, installation, fetching examples, and operational command catalogs to the root Axolotl skill or `cli-and-operations` when present.

## Evidence Notes

This guidance is distilled from Axolotl model architecture docs, multimodal/quantization/attention/LoRA docs, loader and schema behavior, model-specific monkeypatches, examples, and tests. The inspection environment proved package metadata and namespace import only; do not claim live model downloads, training, inference, or GPU runtime verification unless the user runs those checks separately.
