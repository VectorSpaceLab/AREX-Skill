---
name: rank_and_recovery_evaluation
description: Compute effective dimension, choose a bounded Nyström rank, and evaluate recovery traces for condition-number and PCG iteration improvements.
---

# Rank And Recovery Evaluation

Use this skill to connect a Nyström PCG experiment to the paper's rank/effective-dimension theory and reported convergence metrics. It owns recovery acceptance predicates, not the solver itself.

## Inputs

- Matrix eigenvalues or a dense PSD matrix.
- Regularization `mu`.
- Candidate rank cap or chosen rank.
- CG and Nyström PCG traces.
- Dense condition-number diagnostics when available.

## Outputs

- Effective dimension `sum(lambda_i / (lambda_i + mu))`.
- Selected rank and rationale.
- Metrics: iteration reduction, residual status, condition-number reduction, and mechanism flags.
- Boolean acceptance for a declared proxy recovery.

## Workflow

1. Compute effective dimension from eigenvalues.
2. Choose rank near `2 ceil(1.5 d_eff) + 1` when feasible, otherwise cap and record the cap.
3. Compare CG and Nyström PCG traces under the same tolerance.
4. For recovery confidence, include at least one low-rank or stress-seed ablation when time permits, and verify the selected rank improves conditioning over a weaker sketch.
5. Require PCG convergence, fewer PCG iterations, condition-number reduction, and positive mechanism checks.
6. Return an auditable decision and gap explanation.

## Validation

Run:

```bash
python scripts/evaluate_recovery.py --self-test
python tests/test_evaluate_recovery.py
```

The tests check effective dimension calculation, rank capping, acceptance of a valid trace, and rejection of no-improvement traces.

## Limitations

This skill can accept a soft-mode proxy only when the experiment explicitly declares why full paper-scale data are unavailable and logs mechanism checks.
