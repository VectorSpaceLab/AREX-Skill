---
name: cad_logit_adjustment
description: Apply the Context-aware Decoding contrastive logit formula and report mechanism diagnostics for recovery experiments.
---

# CAD Logit Adjustment

Use this skill for the paper's core next-token transformation: `adjusted = (1 + alpha) * logits(context, query, prefix) - alpha * logits(query, prefix)`. It does not construct prompts or score final answers.

## Inputs
- Context-conditioned logits as a token-to-score mapping.
- Query-only/prior logits as a token-to-score mapping.
- `alpha`, usually `0.5` for summarization or `1.0` for knowledge-conflict tasks.

## Outputs
Adjusted logits over the shared vocabulary plus diagnostics: alpha, regular argmax, prior argmax, adjusted argmax, and whether CAD changed the selected token.

## Workflow
1. Verify identical vocabularies.
2. Compute the CAD formula for each token.
3. Preserve logits without softmax unless probabilities are requested downstream.
4. Report argmax diagnostics for mechanism checks.

## Validation
Run `tests/test_logit_adjustment.py` or Distiller validation.

## Limitations
This script works on one decoding step; generation loops should call it repeatedly with updated prefixes.
