---
name: fudge_logit_rescoring
description: Apply the FUDGE decoding rule by combining base candidate logits with future-discriminator probabilities and renormalizing.
---

# FUDGE Logit Rescoring

Use this skill when a base autoregressive generator supplies candidate next-token logits and a future discriminator can score each candidate-extended prefix. The skill implements `logit' = base_logit + strength * log P(attribute | prefix+candidate)`.

## Inputs
- `prefix_tokens`.
- Mapping of candidate token to base logit.
- Mapping/callable of candidate token to future probability.
- Optional `strength`, `top_k`, and clipping epsilon.

## Outputs
- Normalized probabilities over retained candidates.
- Audit trace with base logit, future probability, future log score, adjusted logit, and final probability.

## Workflow
1. Restrict to top-k base candidates if requested.
2. Score each extended prefix with the future discriminator.
3. Clip probabilities for numerical safety.
4. Add future log scores to base logits.
5. Softmax over retained candidates.
6. Inspect the audit trace before claiming FUDGE was used.

## Validation
Run `python tests/test_rescoring.py`.

## Limitations
This helper does not load a language model. It is a deterministic FUDGE rescoring kernel.
