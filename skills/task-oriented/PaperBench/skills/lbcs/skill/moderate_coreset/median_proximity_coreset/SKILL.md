---
name: median_proximity_coreset
description: Select Moderate-DS coresets by keeping examples whose scalar scores are closest to the score median.
---

# Median Proximity Coreset

Use this skill after scores have been computed for candidate examples. It implements the paper's moderate coreset rule: sort by closeness to the score median rather than selecting the smallest or largest scores. Do not use this skill to compute representation scores or to claim downstream performance.

## Inputs
- A list of score records containing `id` and numeric `score`.
- Either an integer `size` or a ratio convertible to a target size by the caller.

## Outputs
- Selected ids.
- The median score.
- Ranked proximity diagnostics with deterministic tie-breaking.

## Workflow
1. Validate all scores and requested size.
2. Compute the conventional median of all scores.
3. Rank records by absolute distance to the median, then by score and id for deterministic ties.
4. Return exactly the requested number of selected ids.

## Validation
Run `python scripts/select_median_coreset.py --self-test`. Tests include even medians, stable ties, and invalid sizes.

## Limitations
The skill operates on scalar scores only. A future run should combine it with a scoring skill and an evaluation skill for complete Moderate-DS recovery.
