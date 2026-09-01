---
name: pplm_candidate_reranking
description: Use when generated candidates must be ranked by attribute likelihood with Dist-n diversity filtering as in PPLM BCR.
---

# PPLM Candidate Reranking

Use this skill for PPLM BR/BCR-style candidate selection.

## Inputs
- Candidate token sequences.
- Attribute scores where larger is better.
- Minimum Dist-n diversity threshold.

## Outputs
- Dist-1/2/3 metrics.
- Filtered ranked list.
- Selected candidate and reason.

## Workflow
1. Compute Dist-n as unique n-grams divided by total n-grams.
2. Filter candidates below the requested Dist threshold.
3. Select the highest attribute score among surviving candidates.
4. If all candidates fail diversity, select the highest score and record fallback.

## Validation
Run `python tests/test_candidate_reranking.py`.

## Limitations
Reduced proxy implementations must declare that they are not full GPT-2 345M reproduction.
