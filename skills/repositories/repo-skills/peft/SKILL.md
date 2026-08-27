---
name: peft
description: "Use PEFT for parameter-efficient fine-tuning adapters, LoRA and
  quantized workflows, prompt and soft methods, specialized tuners,
  save/load/merge operations, training integrations, and PEFT repository
  development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PEFT

Use this skill when a task names Hugging Face PEFT, `peft`, `PeftModel`, `PeftConfig`, `get_peft_model`, LoRA/QLoRA, prompt tuning, adapter checkpoints, adapter merging, PEFT training integrations, or changes to the PEFT repository.

## Route By Task

- **Core adapter setup**: use `sub-skills/adapter-core/SKILL.md` for `PeftConfig`, `TaskType`, `PeftType`, `get_peft_model`, adapter lifecycle, trainable status, custom model targeting, and low-level injection.
- **LoRA and quantization**: use `sub-skills/lora-and-quantization/SKILL.md` for `LoraConfig`, QLoRA, DoRA, rsLoRA, PiSSA, CorDA, LoftQ, QALoRA, trainable tokens, and quantized-base compatibility.
- **Prompt and soft methods**: use `sub-skills/prompt-and-soft-methods/SKILL.md` for prompt tuning, prefix tuning, P-tuning, multitask prompt tuning, CPT, adaption prompt, cartridge, and trainable-token prompt workflows.
- **Specialized tuners**: use `sub-skills/specialized-tuners/SKILL.md` for IA3, BOFT, OFT, LoHa, LoKr, VeRA/PVeRA, VBLoRA, XLora, FourierFT, HRA/HiRA/SHiRA, RandLoRA, and other non-LoRA/non-prompt method families.
- **Save, load, merge, and deploy**: use `sub-skills/save-load-merge/SKILL.md` for adapter checkpoint layout, `save_pretrained`, `from_pretrained`, `AutoPeftModel*`, `merge_and_unload`, hotswap, mixed adapters, Hub/local loading, and conversion.
- **Training integrations**: use `sub-skills/training-and-integrations/SKILL.md` for Transformers Trainer, Accelerate, FSDP, DeepSpeed, TRL SFT, Diffusers examples, memory-efficient training, and `torch.compile` caveats.
- **PEFT repository development**: use `sub-skills/repo-development/SKILL.md` for contribution policy, new tuner registration, test selection, style/quality commands, docs, and AI-assisted PR disclosure rules.

## Fast Start

1. Verify imports with `sub-skills/adapter-core/scripts/check_peft_env.py` in an environment that has `peft`, `torch`, `transformers`, and `accelerate`.
2. Decide the adapter family before writing training code. LoRA and quantized workflows have different constraints from prompt-learning and specialized tuners.
3. Keep base-model loading, adapter construction, training launcher settings, and checkpoint save/merge decisions separate so each can be reviewed.
4. Avoid downloading large models in smoke tests. Use config construction, helper scripts, or tiny custom `torch.nn.Module` checks when possible.

## References

- `references/workflow-overview.md` gives a root-level decision map across adapter lifecycle stages.
- `references/troubleshooting.md` covers cross-cutting install/import, optional backend, target-module, checkpoint, merge, and training failures.
- `references/repo-provenance.md` records the source revision and extraction evidence.
