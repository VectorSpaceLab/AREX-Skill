---
name: score_masking
description: Compute deterministic score-based pruning masks using top-v or threshold rules for movement-pruning style experiments.
---

# Score-Based Pruning Masks

Use this skill when a pruning experiment needs to convert importance scores into binary masks without depending on a paper repository. Do not use it for structured head/layer pruning unless the caller has already reduced each structure to one scalar score.

## Inputs
- `scores`: a rectangular nested list or flat list of numeric scores.
- `mode`: `top_v` or `threshold`.
- `keep_ratio`: required for `top_v`, from 0 to 1.
- `threshold`: required for `threshold`; entries are kept only when `score > threshold`.

## Outputs
A JSON-compatible object containing `mask`, `metadata`, and a flattened `kept_indices` list. The mask has the same shape as the input scores.

## Workflow
1. Validate numeric score shape.
2. Flatten scores in row-major order.
3. For `top_v`, keep `ceil(n * keep_ratio)` entries after sorting by descending score and then stable index.
4. For `threshold`, keep scores strictly greater than the threshold.
5. Restore the original shape and report sparsity metadata.

This implements the paper abstraction `M = Top_v(S)` for hard movement pruning and `M = (S > tau)` for soft movement pruning.

## Validation
Run `python tests/test_score_masking.py` or validate the full skill tree. The tests cover ties, negative scores, zero/full keep ratios, and strict threshold equality.

## Limitations
The skill only computes masks. It does not train scores or patch neural-network layers.
