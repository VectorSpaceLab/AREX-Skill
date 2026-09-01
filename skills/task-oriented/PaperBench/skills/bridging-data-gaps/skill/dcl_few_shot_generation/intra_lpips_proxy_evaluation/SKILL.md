---
name: intra_lpips_proxy_evaluation
description: Compute a deterministic intra-cluster diversity proxy mirroring intra-LPIPS evaluation for reduced few-shot generation recovery.
---

# Intra-LPIPS Proxy Evaluation

Use this skill when LPIPS networks are unavailable but recovery needs to preserve the paper's intra-cluster diversity evaluation structure. It computes nearest-target clusters and average within-cluster Euclidean distances over features. Do not report it as real LPIPS.

## Inputs
- Generated feature samples.
- Few target exemplar features.

## Outputs
- Average intra-cluster distance proxy.
- Cluster assignments and pair counts.

## Workflow
1. Assign each generated feature to its nearest target exemplar.
2. For each cluster, compute all pairwise generated-feature distances.
3. Average distances across non-singleton clusters.
4. Return zero for exact memorization or singleton-only clusters.

## Validation
Run `python tests/test_intra_lpips_proxy_evaluation.py` from this skill directory.

## Limitations
This metric is only a feature-distance proxy for intra-LPIPS; it is useful for mechanism checks but not comparable to paper LPIPS values.


## Refinement Note
Include a memorization ablation: exact copies of target exemplars should have lower or zero intra-cluster diversity than adapted generated features.
