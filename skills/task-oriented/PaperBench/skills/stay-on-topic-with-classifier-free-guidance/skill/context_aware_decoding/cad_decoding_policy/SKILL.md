---
name: cad_decoding_policy
description: Select tokens from regular or CAD-adjusted logits using comparable greedy or top-p decoding policies.
---

# CAD Decoding Policy

Use this skill after CAD logit adjustment when selecting the next token. It preserves the paper's rule that CAD changes the logits while the outer decoding strategy remains comparable to the regular baseline.

## Inputs
- Logit mapping from token to score.
- `mode`: `greedy` or `top_p`.
- Optional `top_p` and random seed.

## Outputs
A selection trace containing selected token, probabilities, candidate set, and mode.

## Workflow
1. Convert logits to probabilities with softmax.
2. Greedy mode chooses the highest-scoring token deterministically.
3. Top-p mode keeps the minimal nucleus with cumulative mass at least `top_p` and samples with the supplied seed.
4. Return the candidate set for audit.

## Validation
Run `tests/test_decoding_policy.py` or Distiller validation.

## Limitations
This skill does not compute CAD logits; it consumes whichever logits are supplied.
