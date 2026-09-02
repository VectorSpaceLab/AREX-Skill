---
name: coherence_boosted_scoring
description: Apply the coherence boosting log-linear scoring rule to full-context and premise-free answer likelihoods.
---

# Coherence Boosted Scoring

Use this skill when you already have candidate log likelihoods under a full context and a premise-free context and need the paper's inference-time correction.

## Inputs
- Equal-length lists of full-context and premise-free log likelihoods.
- A real-valued `alpha`; negative values discount premise-free priors.

## Outputs
- Combined scores `full_logprob + alpha * short_logprob`.
- Predicted candidate index and margin diagnostics.

## Workflow
1. Validate equal list lengths and finite numeric values.
2. Compute boosted scores in the log domain.
3. Return the argmax, preserving candidate order.
4. Record whether alpha is negative, zero, or positive for mechanism evidence.

## Validation
Run the deterministic tests in `tests/test_boosted_scoring.py`.

## Limitations
This skill does not estimate likelihoods or select alpha. It only implements the paper's scoring equation.
