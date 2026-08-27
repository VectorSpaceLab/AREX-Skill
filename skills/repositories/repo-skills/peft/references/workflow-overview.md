# PEFT Workflow Overview

| Stage | Owning sub-skill | Key checks |
| --- | --- | --- |
| Choose adapter type | `adapter-core`, `lora-and-quantization`, `prompt-and-soft-methods`, `specialized-tuners` | Match task type, method family, model architecture, target modules, and optional dependency constraints. |
| Wrap base model | `adapter-core` | Use `get_peft_model`, explicit `target_modules` for custom models, and status helpers before training. |
| Quantized training | `lora-and-quantization`, `training-and-integrations` | Prepare k-bit models before wrapping, verify backend availability, and keep distributed settings compatible. |
| Train | `training-and-integrations` | Apply PEFT before trainer/accelerator preparation, keep save semantics rank-safe, and avoid running large examples as smoke tests. |
| Save/load/share | `save-load-merge` | Check `adapter_config.json`, adapter weights, base model reference, embedding save decisions, and adapter names. |
| Merge/deploy | `save-load-merge` | Use merge only for supported methods/settings; keep adapter checkpoints when continued PEFT operations are needed. |
| Contribute upstream | `repo-development` | Follow PEFT agent contribution policy, approval/disclosure rules, tests, style, and docs requirements. |
