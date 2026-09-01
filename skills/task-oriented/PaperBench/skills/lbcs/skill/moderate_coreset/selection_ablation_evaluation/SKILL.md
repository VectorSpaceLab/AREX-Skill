---
name: selection_ablation_evaluation
description: Compare Moderate-DS median selection against center-close, far-from-center, and two-end score policies.
---

# Selection Ablation Evaluation

Use this skill to test whether a selected coreset follows the paper's intended balance between centrality and diversity. It is appropriate for synthetic fixtures, representation datasets, and recovery harnesses that already have per-record scores. It should not compute hidden representations or replace full downstream model evaluation.

## Inputs
- Score records with stable `id`, `label`, and numeric `score`.
- Selected ids for one or more policies.

## Outputs
- Per-policy mean score, score spread, class coverage, balance score, and advantage diagnostics.

## Workflow
1. Build baseline selections for center-close, far-from-center, and two-end policies when requested.
2. Compute centrality as closeness to the full score median and diversity as selected-score spread.
3. Combine these into a deterministic balance metric suitable for fast proxy recovery.
4. Report whether the moderate policy improves over the strongest extreme baseline.

## Validation
Run `python scripts/evaluate_selection_policies.py --self-test`. The smoke fixture is designed so the median policy has a positive mechanism-faithful advantage.

## Limitations
The balance metric is a proxy diagnostic, not a replacement for CIFAR or ImageNet test accuracy.
