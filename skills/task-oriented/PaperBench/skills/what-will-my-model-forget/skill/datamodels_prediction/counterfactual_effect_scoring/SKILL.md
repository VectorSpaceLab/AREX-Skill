---
name: counterfactual_effect_scoring
description: Estimate training-data removal effects by summing linear datamodel weights and evaluating counterfactual correlations.
---

# Counterfactual Effect Scoring

Use this skill after a linear datamodel has produced per-training-example weights. It estimates how removing a candidate group of examples changes a fixed target outcome.

## Inputs

- Datamodel weights `theta`.
- Candidate removal sets as index lists.
- Optional actual counterfactual effects for validation.

## Outputs

- Predicted effect per removal set.
- Ranked influential training indices.
- Pearson correlation with actual effects when labels are supplied.

## Workflow

1. Validate every removal index against the weight vector.
2. Sum `theta[i]` over each removal set.
3. Rank individual examples by signed or absolute weight.
4. Compare predicted and actual effects if actual counterfactual outcomes are available.

## Validation

Run:

```bash
python scripts/score_counterfactuals.py --demo
python tests/test_score_counterfactuals.py
```

## Limitations

The score is a linear extrapolation from the datamodel. Large or distribution-shifted removal sets should be declared as counterfactual extrapolation.
