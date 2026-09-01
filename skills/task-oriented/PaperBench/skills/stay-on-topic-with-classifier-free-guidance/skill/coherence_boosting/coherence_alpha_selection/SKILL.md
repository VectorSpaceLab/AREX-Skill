---
name: coherence_alpha_selection
description: Select a coherence boosting alpha from cached validation likelihoods without model finetuning.
---

# Coherence Alpha Selection

Use this skill when validation examples contain full-context and premise-free candidate log likelihoods and labels. It implements the paper's one-pass validation-grid choice of alpha.

## Inputs
- Validation records with `full_logprobs`, `short_logprobs`, and `label`.
- A numeric alpha grid.

## Outputs
- Best alpha, accuracy curve, and deterministic tie-breaking notes.

## Workflow
1. For each alpha, call the boosted scoring rule.
2. Compute validation accuracy.
3. Choose the highest accuracy; ties prefer the alpha with smaller absolute value, then smaller numeric value for reproducibility.
4. Return the full curve for audit.

## Validation
Run `tests/test_alpha_selection.py`.

## Limitations
The skill assumes likelihoods have already been computed by a frozen LM or a declared proxy scorer.
