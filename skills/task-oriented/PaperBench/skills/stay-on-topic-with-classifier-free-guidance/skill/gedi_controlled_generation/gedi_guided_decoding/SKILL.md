---
name: gedi_guided_decoding
description: Reweight base language-model token probabilities with GeDi posteriors and apply GeDi cumulative-mass filtering for controlled decoding.
---

# GeDi Guided Decoding

## When to use
Use this skill when candidate next-token base log probabilities and GeDi desired-class posteriors are available and you need to produce a guided token distribution or greedy token choice.

## Inputs
- Candidate token strings or ids.
- Base LM next-token log probabilities.
- Desired-class posterior probabilities from a GeDi posterior computation.
- Steering weight `omega`.
- Cumulative-mass threshold `rho`.

## Outputs
- Guided probabilities.
- Retained-token mask after posterior sorting/filtering.
- Selected token for greedy decoding.

## Workflow
1. Compute guided logits as `base_logprob + omega * log(posterior)`.
2. Normalize the logits with log-sum-exp.
3. Sort tokens by GeDi posterior descending.
4. Keep the smallest prefix whose guided probability mass is at least `rho`.
5. Renormalize retained probabilities and select greedily unless sampling is explicitly requested.

## Validation
Run:

```bash
python tests/test_decoding.py
```

## Limitations
This skill does not compute posteriors or call a model; it consumes already-computed candidate posteriors.
