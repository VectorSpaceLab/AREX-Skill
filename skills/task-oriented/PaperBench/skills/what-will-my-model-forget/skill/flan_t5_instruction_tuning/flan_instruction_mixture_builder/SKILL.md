---
name: flan_instruction_mixture_builder
description: Build FLAN-style multi-source instruction-finetuning mixtures while excluding held-out evaluation tasks and auditing source/CoT coverage.
---

# FLAN Instruction Mixture Builder

Use this skill when constructing an instruction-finetuning mixture inspired by Scaling Instruction-Finetuned Language Models. Do not use it for evaluation scoring or prompt rendering.

## Inputs

- Task records with `source`, `task_id`, `benchmark`, `examples`, and optional `cot` fields.
- Held-out task ids, benchmark names, or aliases that must be excluded.

## Outputs

- Filtered mixture records.
- Audit JSON with retained ids, excluded ids/reasons, per-source counts, and CoT counts.

## Workflow

1. Normalize task ids and benchmark names.
2. Exclude tasks whose id or benchmark matches the held-out set.
3. Preserve source labels and CoT flags for downstream checks.
4. Emit retained and excluded task audit data.

## Validation

Run `python tests/test_mixture_builder.py`.

## Limitations

This skill enforces bounded recovery invariants and does not reproduce the full 1.8K-task FLAN mixture.
