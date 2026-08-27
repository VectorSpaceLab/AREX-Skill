---
name: models-and-modules
description: "Use torchtune model/tokenizer builders, PEFT modules, losses,
  conversion utilities, and modeling components safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# models-and-modules

Use this sub-skill when a torchtune task is about model-family builders, tokenizer/model-transform builders, LoRA/QLoRA/DoRA adapters, transformer/attention/loss modules, MoE and low-precision pieces, state-dict conversion, or custom model components.

## Route Here For

- Choosing public `_component_` dotpaths under `torchtune.models.*` or `torchtune.modules.*` for YAML configs or custom code.
- Pairing model builders with matching tokenizer or multimodal transform builders before dataset or recipe wiring.
- Adding LoRA, QLoRA, DoRA, QAT-LoRA, adapter-state extraction, adapter merging, or trainable-parameter setup.
- Using torchtune modeling blocks such as attention, decoder layers, KV cache, RoPE, RMSNorm, chunked/KL losses, MoE experts, and NF4 linear layers.
- Converting state-dict key formats between torchtune, Meta, Hugging Face, and PEFT adapter conventions.
- Writing custom config-friendly builders without importing the intentionally non-importable `recipes` package.

## Standard Workflow

1. Identify the model family and checkpoint provenance before choosing builder names; use [model catalog](references/model-catalog.md) for public dotpaths.
2. Match the tokenizer or model transform to the same family and downloaded artifact layout before training, generation, or dataset transforms.
3. For adapter work, choose a family `lora_*` or `qlora_*` builder first, then use [PEFT and adapters](references/peft-and-adapters.md) for `lora_attn_modules`, trainable params, and merge/export behavior.
4. For custom code, import public modules from `torchtune.models`, `torchtune.modules`, `torchtune.modules.peft`, `torchtune.modules.loss`, or `torchtune.generation`; avoid private underscore dotpaths in configs.
5. Use [module API reference](references/module-api-reference.md) for component signatures, losses, generation helpers, MoE, low precision, and conversion utilities.
6. Diagnose optional dependency, tokenizer, gated checkpoint, LoRA target, QLoRA, and state-dict issues with [troubleshooting](references/troubleshooting.md) before launching expensive jobs.

## Bundled Helper

Run the helper from this sub-skill directory to inspect callable public model exports in the active environment without instantiating large models:

```bash
python scripts/inspect_model_builders.py --families llama3 qwen2_5 --format table
```

It imports family modules, lists callable public exports and signatures, and reports optional-dependency import failures instead of downloading checkpoints or constructing models.

## Read Next

- [Model catalog](references/model-catalog.md) for family builders, tokenizer notes, multimodal transforms, and public dotpath examples.
- [Module API reference](references/module-api-reference.md) for attention/decoder blocks, losses, generation, MoE, low precision, export variants, and conversion functions.
- [PEFT and adapters](references/peft-and-adapters.md) for LoRA/QLoRA/DoRA/QAT-LoRA config patterns and adapter state dict guidance.
- [Troubleshooting](references/troubleshooting.md) for private dotpaths, gated downloads, tokenizer mismatches, adapter target names, QLoRA dependencies, conversion failures, and export variants.
- [data-and-datasets](../data-and-datasets/SKILL.md) for dataset transforms, message schemas, packing, and collators.
- [post-training-recipes](../post-training-recipes/SKILL.md) for recipe selection and training launch planning.
- [inference-evaluation-quantization](../inference-evaluation-quantization/SKILL.md) for generation workflows, evaluation, and post-training quantization routing.
- [cli-and-config](../cli-and-config/SKILL.md) for `tune cp`, `tune cat`, `tune validate`, `_component_`, and override mechanics.

## Guardrails

- Use public dotpaths such as `torchtune.models.llama3.llama3_8b`, not private implementation paths like `torchtune.models.llama3._model_builders.llama3_8b`.
- Do not `import recipes`; use `tune run`, registry names, copied config files, or custom recipe files launched through the CLI.
- Do not instantiate full model builders just to inspect names; use signatures, configs, or the bundled inspection helper.
- Do not leak checkpoint locations, token files, credentials, local environments, or machine-specific paths into reusable configs or skill content.
- Keep dataset schemas in `data-and-datasets`, recipe launch construction in `post-training-recipes`, and generation/evaluation/quantization workflows in `inference-evaluation-quantization`.
