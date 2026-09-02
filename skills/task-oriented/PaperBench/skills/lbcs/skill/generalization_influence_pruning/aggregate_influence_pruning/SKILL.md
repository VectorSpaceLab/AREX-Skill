---
name: aggregate_influence_pruning
description: Select removable data subsets by constraining aggregate influence vector norm instead of ranking independent scalar scores.
---

# Aggregate Influence Pruning

Use this skill after per-example influence vectors have been estimated. It implements the paper's central subset-selection idea: maximize removable cardinality while the norm of the sum of removed influences remains below epsilon.

## Inputs

- Per-example influence vectors with equal dimensionality.
- `epsilon` for generalization-guaranteed pruning or `cardinality` for fixed-size pruning.
- Bounded search mode; exhaustive search is appropriate only for small recovery cases.

## Outputs

- Selected removal indices and binary mask.
- Aggregate influence vector and norm.
- Feasibility and objective metadata.

## Workflow

1. Validate influence vector dimensions and finite values.
2. Enumerate candidate masks for tiny recovery runs, or use a deterministic bounded heuristic for larger runs.
3. Prefer larger feasible subsets; break ties by lower aggregate norm.
4. Save enough metadata to prove joint cancellation was considered.

## Validation

Run `python scripts/prune_by_influence.py --demo` and `python tests/test_prune_by_influence.py` from this skill directory.

## Limitations

The exhaustive implementation is for bounded recovery and testing. Large datasets should use a time-limited heuristic such as simulated annealing while preserving the same objective contract.
