---
name: rlaif_evaluation_metrics
description: Compute RLAIF AI-labeler alignment, pairwise win rate, harmless rate, and proxy target consistency metrics.
---

# RLAIF Evaluation Metrics

Use this skill when interpreting RLAIF labels or reduced recovery outputs. It computes the paper's metric families separately so labeler agreement, policy win rates, and harmlessness rates are not conflated.

Do not use this skill to generate labels, train rewards, or update policies.

## Inputs

- Alignment records with `preference` and `human_label`.
- Win-rate records with `winner` and a target `policy`.
- Harmlessness records with `harmless` booleans.
- Optional target metadata from a module plan or recovery result.

## Outputs

- `alignment_accuracy`, `win_rate`, `harmless_rate`, and sample counts.
- Tie counts for alignment records.
- Target consistency result when metadata is supplied.

## Workflow

1. Convert each soft AI preference into an argmax label.
2. Treat exact soft-label ties as abstentions by default.
3. Average agreement with human labels for AI-labeler alignment.
4. Average policy wins for pairwise win rate.
5. Average harmless booleans for harmless rate.
6. Check target dataset, metric, and paper value consistency when requested.

## Validation

Run:

```bash
python scripts/evaluation_metrics.py --smoke
python tests/test_evaluation_metrics.py
```

The tests cover alignment with ties, win rate, harmless rate, and target metadata consistency.

## Limitations

These metrics are only as meaningful as the records supplied. For proxy recovery, mechanism checks must accompany the metrics.
