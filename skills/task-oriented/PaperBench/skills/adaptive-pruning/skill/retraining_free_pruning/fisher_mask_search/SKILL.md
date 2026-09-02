---
name: fisher_mask_search
description: Select Transformer heads and filters to prune using diagonal Fisher scores under a FLOPs budget.
---

# Fisher Mask Search

Use this skill when implementing post-training structured pruning for Transformers and you need the paper's first stage: a fast binary mask search from diagonal Fisher importance. Do not use it for unstructured weight pruning or when unit costs differ per individual head/filter without adapting the cost model.

## Inputs

- `head_scores`: nonnegative diagonal Fisher importance values for attention heads.
- `filter_scores`: nonnegative diagonal Fisher importance values for feed-forward filters.
- `head_cost`, `filter_cost`: positive per-unit costs.
- `budget`: maximum remaining cost.

## Outputs

- Binary head and filter masks where `1` is kept and `0` is pruned.
- Remaining cost, pruned Fisher loss, and selected kept counts.

## Workflow

1. Validate that scores are nonnegative and costs are positive.
2. Enumerate the number of remaining heads.
3. For each head count, keep the largest feasible number of filters.
4. Prune the least-important units of each type and score the candidate by pruned Fisher loss.
5. Return the minimum-loss feasible mask with deterministic tie breaking.

## Validation

Run `python tests/test_fisher_mask_search.py` or validate the skill tree with `validate_skill_tree.py --run-tests`.
