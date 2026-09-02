---
name: factorized_score_composition
description: Compose F-NPSE and PF-NPSE posterior scores from learned score terms and prior corrections for SBI.
---

# Factorized Score Composition

Use this skill when implementing the central compositional step from F-NPSE or PF-NPSE. It turns score estimates for individual observations or small observation groups into one score for a multi-observation posterior approximation.

Do not use this skill for denoising score training or for sampling. It expects a score predictor to already exist and returns a composed score that a sampler can consume.

## Inputs

- Current `theta`.
- Time index `t` and total diffusion levels `T`.
- Observations for F-NPSE or groups for PF-NPSE.
- Prior score function, such as `-theta` for a standard normal prior.
- Score predictor for one observation or one group.

## Outputs

- Composed score vector.
- Metadata with method, observation count, group count, and prior coefficient.
- Per-term score diagnostics that can be logged for recovery evidence.

## Workflow

For F-NPSE, compute:

```text
((1 - n) * (T - t) / T) * grad_log_prior(theta) + sum_j s(theta, t, x_j)
```

For PF-NPSE, partition observations into groups of size at most `m`, compute `k` groups, and use the same formula with `k` replacing `n` and group score predictions replacing single-observation scores.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

The tests verify the paper formulas, grouping behavior, and invariance to group order for deterministic score terms.

## Limitations

This skill does not decide whether score estimates are accurate. It only enforces the algebraic composition contract from the paper.
