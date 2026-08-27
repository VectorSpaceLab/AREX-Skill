---
name: specialized-tuners
description: "Select, configure, and troubleshoot PEFT's specialized
  non-LoRA/non-prompt tuners such as IA3, BOFT, OFT, LyCORIS-style LoHa/LoKr,
  VeRA/PVeRA, VBLoRA, XLora, LN tuning, FourierFT, FRoD, HRA/HiRA/SHiRA,
  RandLoRA, RoAd, OSF, and newer experimental tuner configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PEFT Specialized Tuners

Use this sub-skill when the user needs a PEFT adapter that is not ordinary LoRA, not a LoRA quantization workflow, and not prompt/soft-prompt tuning. It covers method selection, config-class lookup, target-module planning, compatibility checks, and troubleshooting for specialized tuners.

## Route here for

- IA3, BOFT, OFT, LoHa, LoKr, Poly, Vera/PVera, VBLoRA, XLora, LN tuning, FourierFT, FROD, HRA, Hira, Shira, RandLoRA, Road, WaveFT, OSF, Delora, Gralora, Adamss, Beft, C3A, Lily, MISS, Psoft, Peanut, TinyLoRA, and nearby config/model classes.
- Choosing a non-LoRA alternative when LoRA is too large, too low-rank, unsuitable for heterogeneous serving, or not expressive enough.
- Validating that a method has a public `*Config` class and that its target-module constraints match the base model.
- Debugging method-specific errors such as missing `feedforward_modules`, unsupported layer classes, projection reproducibility, or mixed-adapter incompatibility.

## Route elsewhere

- LoRA, AdaLoRA, DoRA, RS-LoRA, LoRA initialization variants, QLoRA, LoftQ, bitsandbytes quantization, and target-parameter LoRA: use `../lora-and-quantization/SKILL.md`.
- Prompt tuning, prefix tuning, P-tuning, multitask prompt tuning, CPT, trainable tokens, and adaption prompt methods: use `../prompt-and-soft-methods/SKILL.md`.
- Generic `PeftModel`, save/load, adapter naming, hotswapping, merging, and model lifecycle: use `../adapter-core/SKILL.md`.

## Fast workflow

1. Identify the task surface: causal LM, seq2seq LM, sequence/token classification, vision, diffusion, continual learning, multi-adapter serving, or checkpoint-size reduction.
2. Pick a method family from `references/method-catalog.md` instead of mirroring a source folder name mechanically.
3. Confirm the public config class with `references/api-reference.md` or `scripts/list_peft_methods.py --filter <method>`.
4. Set `target_modules` explicitly for custom models; rely on PEFT defaults only when the method documents a mapping for the model family.
5. Use `get_peft_model(base_model, config)` and inspect trainable parameters before training.
6. If the adapter will be mixed with other adapters, check mixed compatibility before promising `adapter_names` batch routing or weighted fusion.

## Minimal patterns

```python
from peft import IA3Config, TaskType, get_peft_model

config = IA3Config(
    task_type=TaskType.CAUSAL_LM,
    target_modules=["q_proj", "v_proj", "fc2"],
    feedforward_modules=["fc2"],
)
model = get_peft_model(base_model, config)
model.print_trainable_parameters()
```

```python
from peft import VeraConfig, get_peft_model

config = VeraConfig(
    target_modules=["q_proj", "v_proj"],
    r=256,
    save_projection=True,
)
model = get_peft_model(base_model, config)
```

## Bundled references

- `references/method-catalog.md`: selection guidance by method family and use case.
- `references/api-reference.md`: config/model class names, common fields, and config naming gotchas.
- `references/troubleshooting.md`: errors and diagnosis for target layers, optional dependencies, mixed adapters, and method constraints.
- `scripts/list_peft_methods.py`: local PEFT introspection helper for `PeftType` and public `*Config` classes.
