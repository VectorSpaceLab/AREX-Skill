---
name: constraint_composition
description: Compose multiple FUDGE future constraints, especially topic-word constraints, by summing weighted log probabilities.
---

# Constraint Composition for Topics

Use this skill when a FUDGE decoder must condition on several target words or independent attributes. For topic control, compute `(lambda/N) * sum_j log P(w_j | prefix+candidate)`.

## Inputs
- Candidate-to-target probability table.
- Ordered list of target words or attributes.
- `lambda_value` and whether to normalize by `N`.

## Outputs
- Composed future log score per candidate.
- Audit contributions per candidate and per target.

## Workflow
1. Ensure every candidate has every target probability.
2. Clip probabilities to avoid log(0).
3. Compute the target weight.
4. Sum weighted log-probability contributions.
5. Pass the composed score to the FUDGE rescoring skill.

## Validation
Run `python tests/test_composition.py`.
