---
name: score_based_subset_selection
description: Select retained and pruned supervised-training examples from EL2N or GraNd scores using deterministic pruning rules.
---

# Score-Based Subset Selection

Use this skill after EL2N or GraNd scores have been computed and a pruning experiment needs a reproducible retained subset. It implements the paper's standard rule of pruning low-score examples and retaining high-score examples, plus an offset-window mode for noise-analysis style checks.

## Inputs
- Example records with `id` and numeric `score`.
- `retain_fraction` or `retain_count`.
- Optional `mode`: `high_score` or `offset_window`.
- Optional `offset_fraction` for offset-window selection.

## Outputs
- Selected example ids.
- Pruned example ids.
- Selection statistics and tie policy.

## Workflow
1. Validate unique ids and finite scores.
2. Sort by descending score for standard high-score retention.
3. Convert fraction to an exact selected count with floor and minimum one.
4. Apply deterministic tie-breaking by id string.
5. Return selected/pruned complements and score-boundary statistics.

## Validation
Run:

```bash
python tests/test_selection.py
python scripts/select_subset.py --fixture
```

## Limitations
- This skill consumes scores; it does not compute EL2N/GraNd.
- It does not train models or decide whether final accuracy is acceptable.
