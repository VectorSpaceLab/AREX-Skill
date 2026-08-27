---
name: preference-tuning
description: "Guides agents configuring Axolotl DPO, IPO, KTO, ORPO, SimPO,
  reward model, and process reward model workflows with preference data checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Preference Tuning

Use this sub-skill when the task is about Axolotl preference-tuning or reward-model workflows, including DPO configs, IPO loss, KTO binary-label data, ORPO or SimPO single-stage alignment, chosen/rejected preference datasets, outcome reward models, and process reward models.

## Route By Task

- For method selection and config skeletons, read [references/workflows.md](references/workflows.md).
- For required record shapes, field mappings, and local JSON/JSONL checks, read [references/data-formats.md](references/data-formats.md) and run [scripts/check_preference_dataset.py](scripts/check_preference_dataset.py).
- For errors around missing columns, swapped labels, KTO labels, reference-model memory, packing, sequence length, loss types, reward-model heads, or PRM data, read [references/troubleshooting.md](references/troubleshooting.md).

## Quick Workflow

1. Pick the method before editing YAML: DPO for paired chosen/rejected data, IPO as DPO with `dpo_loss_type: ["ipo"]`, KTO for unpaired completion plus binary `label`, ORPO for paired data without a reference model, SimPO for paired length-robust no-reference training, reward model for scoring whole responses, and process reward model for step-level scoring.
2. Set the Axolotl YAML fields that define the workflow: `rl` for DPO/KTO/ORPO/SimPO, `dpo_loss_type` and `dpo_loss_weights` only with `rl: dpo`, `reward_model: true` for outcome reward models, or `process_reward_model: true` for token-level process reward models.
3. Keep preference RL configs incompatible with packing: use `sample_packing: false`; for KTO also use `remove_unused_columns: false`.
4. Validate a small local dataset fixture before training with `python scripts/check_preference_dataset.py --mode dpo --input sample.jsonl` or `python scripts/check_preference_dataset.py --mode kto --input sample.jsonl`.
5. Use `axolotl preprocess config.yaml` first to surface config and tokenization errors; use `axolotl preprocess config.yaml --debug` when label masking or chat-template output is unclear.
6. Use `axolotl train config.yaml` only after the config and a representative data sample are consistent.

## Boundaries

- This sub-skill owns offline preference-tuning, DPO/IPO/KTO/ORPO/SimPO data fields, reward-model and process-reward-model config shape, and preference-specific troubleshooting.
- Route online GRPO, GDPO, EBFT, vLLM rollout loops, custom reward functions, and `axolotl vllm-serve` orchestration to the sibling `rl-and-rewards` sub-skill.
- Route generic `chat_template` mechanics, dataset loading, config schema discovery, and non-preference data conversion to `data-and-configs`.
- Route base model loading, LoRA/QLoRA adapter choices, tokenizer templates, and model architecture quirks to `model-loading-and-adapters`.
- Route DeepSpeed, FSDP, multi-GPU launch, throughput, and hardware placement to `distributed-and-performance`.

## Evidence Notes

This guidance is distilled from Axolotl agent RLHF docs, reward-modelling docs, config schemas, prompt strategies, examples, and tests. It does not claim live training verification; expensive ML runtime checks remain native verification candidates for the integrated repo skill.
