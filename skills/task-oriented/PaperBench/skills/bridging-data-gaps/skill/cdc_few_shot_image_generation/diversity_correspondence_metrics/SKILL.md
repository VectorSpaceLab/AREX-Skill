---
name: diversity_correspondence_metrics
description: Compute diversity and correspondence diagnostics for few-shot image generation recovery experiments.
---

# Diversity and Correspondence Metrics

Use this skill when evaluating a few-shot generator adaptation run where overfitting and correspondence preservation matter. It provides deterministic vector analogues of the paper's intra-cluster LPIPS diversity and source-target correspondence analysis.

## Inputs
- Generated feature vectors.
- Target anchor vectors for nearest-anchor cluster assignment.
- Optional source and adapted vectors for pairwise similarity-correlation analysis.

## Outputs
- Average intra-cluster pairwise distance.
- Cluster sizes and assignments.
- Pairwise similarity correlation between source and adapted features.
- A concise metric summary for analysis artifacts.

## Workflow
1. Assign every generated vector to the nearest target anchor.
2. Compute all pairwise Euclidean distances inside each non-singleton cluster.
3. Average cluster distances, treating singleton clusters as zero-diversity evidence.
4. If source and adapted features are present, compute correlation between their pairwise cosine similarity lists.
5. Report numeric metrics and preserve enough assignments for debugging.

## Validation
Run `python tests/test_metrics.py` or validate this skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill uses generic vector distances in reduced recovery. Full paper-level evaluation should replace them with LPIPS/FID when the image stack and datasets are available.
