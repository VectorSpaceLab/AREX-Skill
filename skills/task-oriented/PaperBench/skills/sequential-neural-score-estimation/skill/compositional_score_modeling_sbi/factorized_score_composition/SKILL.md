---
name: factorized_score_composition
description: Compose F-NPSE and PF-NPSE posterior scores from prior corrections and per-condition score estimates.
---

# Factorized Score Composition

Use this skill when implementing or auditing the core F-NPSE/PF-NPSE inference-time score. It should be called before sampling so the recovery can prove that additive score composition, not duplicated harness logic, produced the score.

## Inputs

- Current `theta` vector.
- A progress value `(T - t) / T` in `[0, 1]`.
- Per-observation scores for F-NPSE, or per-subset scores for PF-NPSE.
- Prior score vector, typically `-theta` under standard-normal reparameterization.
- Condition count: number of observations for F-NPSE or number of subsets for PF-NPSE.

## Outputs

- Composed score vector.
- Trace with score sum, prior correction, condition count, progress, and mode.

## Workflow

1. Validate all score vectors have the same dimensionality.
2. Sum learned condition scores.
3. Compute the correction `(1 - condition_count) * progress * prior_score`.
4. Add the correction to the score sum.
5. Return a trace so downstream recovery can verify the sign and count semantics.

## Validation

Run `python tests/test_factorized_score_composition.py` or the Distiller skill-tree validator.

## Limitations

This skill composes supplied score estimates. It does not train the score network and does not sample posterior particles by itself.
