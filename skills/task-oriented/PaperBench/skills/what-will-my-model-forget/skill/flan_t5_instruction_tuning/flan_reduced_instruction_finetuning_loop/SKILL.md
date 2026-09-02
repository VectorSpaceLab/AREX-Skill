---
name: flan_reduced_instruction_finetuning_loop
description: Execute a bounded optimizer-based proxy for FLAN instruction finetuning and record loss plus parameter-change evidence.
---

# FLAN Reduced Instruction Finetuning Loop

Use this skill when full FLAN-T5 finetuning is unavailable but soft-mode recovery permits a declared proxy.

## Inputs

- Formatted prompt/completion records.
- Learning rate and step budget.

## Outputs

- Training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and optimizer flags.

## Workflow

1. Convert records to deterministic features.
2. Compute logistic loss.
3. Apply gradient steps.
4. Save before/after parameter evidence.

## Validation

Run `python tests/test_training_loop.py`.

## Limitations

This validates optimization mechanics but is not full large-model FLAN training.
