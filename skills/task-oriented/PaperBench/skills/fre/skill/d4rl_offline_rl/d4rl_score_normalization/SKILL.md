---
name: d4rl_score_normalization
description: Compute and audit D4RL normalized returns from raw, random-baseline, and expert-reference scores.
---

# D4RL Score Normalization

Use this skill when reporting or checking D4RL-style benchmark scores across tasks with different raw return scales. Do not use it as evidence that offline training was faithful; combine it with dataset and recovery-harness checks.

## Inputs

- `score`: raw policy return.
- `random_score`: return assigned to the 0-point reference.
- `expert_score`: return assigned to the 100-point reference.

## Outputs

- `normalized_score` using `100 * (score - random_score) / (expert_score - random_score)`.
- `diagnostics` with denominator, endpoint interpretation, and extrapolation flags.

## Workflow

1. Parse all values as floats.
2. Reject equal random and expert scores because the normalization denominator is zero.
3. Compute the normalized score with the D4RL formula.
4. Preserve raw inputs in the result for reproducibility.
5. Flag scores below random or above expert without clipping them.

## Validation

Run `python scripts/normalize_score.py --score 5 --random-score 0 --expert-score 10`. The tests cover random, expert, midpoint, extrapolated, and degenerate baseline cases.

## Limitations

This skill does not choose environment-specific reference scores. The caller must provide the paper, benchmark, or recovery-target baselines.
