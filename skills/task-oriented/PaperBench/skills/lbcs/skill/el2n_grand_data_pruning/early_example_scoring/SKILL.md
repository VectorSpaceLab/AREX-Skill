---
name: early_example_scoring
description: Compute EL2N and GraNd example-importance scores for supervised classification pruning experiments.
---

# Early Example Scoring

Use this skill when a recovery or experiment needs paper-faithful per-example scores from "Deep Learning on a Data Diet": EL2N from class probabilities and labels, or GraNd from per-example gradient vectors. Do not use it to choose subsets or report final model accuracy; downstream selection and evaluation own those steps.

## Inputs
- Probability rows shaped as `n_examples x n_classes`.
- Labels as integer class ids or one-hot rows.
- Optional multiple probability runs for score averaging.
- Optional per-example gradient vectors for GraNd.

## Outputs
- Per-example EL2N scores `||p_i - one_hot(y_i)||_2`.
- Averaged EL2N scores across independent runs.
- Per-example GraNd scores from gradient-vector norms.
- JSON diagnostics from the CLI.

## Workflow
1. Validate finite probability rows and labels.
2. Convert integer labels to one-hot rows.
3. Compute EL2N with Euclidean norm of probability error.
4. Average scores over repeated runs when provided.
5. Compute GraNd as gradient-vector Euclidean norm when gradients are available.

## Validation
Run:

```bash
python tests/test_scoring.py
python scripts/score_examples.py --fixture
```

## Limitations
- The script expects probabilities, not raw logits.
- It does not normalize invalid probability rows automatically.
- It does not sort, prune, or train models.
