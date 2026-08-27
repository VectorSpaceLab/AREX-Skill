---
name: adaptation-and-training
description: "Route AdaptLLM, Instruction Pre-Training, PDS data selection,
  ResLoRA, and Learning Law tasks into safe planning and self-contained
  helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# adaptation-and-training

Use this sub-skill for domain adaptation, instruction augmentation, data-selection training, ResLoRA wrapper planning, and Learning Law policy optimization.

## Use when

- A task asks to convert raw domain text into reading-comprehension style data.
- A task asks to synthesize instruction-augmented corpora with a vLLM-based planner.
- A task asks to plan or stage the optimal-control PDS pipeline.
- A task asks to validate ResLoRA flag combinations or target-module mapping.
- A task asks to understand Learning Law optimization or evaluation stages.

## Route elsewhere

- MiniLLM, DPKD, or Tuna distillation tasks go to `../distillation-and-post-training/SKILL.md`.
- VeRL-style RL or experiential-learning tasks go to `../rl-experiential-learning/SKILL.md`.

## What this sub-skill provides

- `references/domain-adaptation-workflows.md` for AdaptLLM-style corpus conversion and domain inference planning.
- `references/instruction-and-data-selection.md` for instruction augmentation and the PDS stage map.
- `references/reslora-and-learning-law.md` for ResLoRA and Learning Law planning.
- `references/troubleshooting.md` for cross-cutting failures and exclusion boundaries.
- `scripts/raw_to_reading_comprehension.py` for a tiny, safe corpus transformer.
- `scripts/pds_pipeline_planner.py` for a stage checklist and path-placeholder validator.
- `scripts/reslora_config_check.py` for ResLoRA config validation.

## Operating rule

Keep heavy training, large data downloads, remote inference, and cluster launches out of this skill. Use the bundled scripts to plan or validate inputs, then hand off full execution to a later researcher session only when the required environment is already available.
