---
name: msfm_batch_coupling
description: Construct uniform and exact small-batch BatchOT couplings for Multisample Flow Matching recovery and tests.
---

# MSFM Batch Coupling

Use this skill when a workflow needs the Multisample Flow Matching pairing step: two equal-size minibatches are converted into either a uniform/independent CondOT baseline or an exact small-batch BatchOT assignment.

Do not use this skill for large production batches unless the exhaustive `batch_ot` implementation is replaced by a scalable assignment or Sinkhorn solver.

## Inputs

- Source batch: JSON list of numeric vectors.
- Target batch: JSON list of numeric vectors with the same length and dimension.
- Method: `uniform` or `batch_ot`.

## Outputs

- Pair indices.
- Mean squared transport cost.
- Coupling matrix and row/column marginal checks.

## Workflow

1. Validate non-empty equal-size source and target batches.
2. Compute pairwise squared Euclidean costs.
3. For `uniform`, report the independent expected cost and a uniform doubly stochastic matrix.
4. For `batch_ot`, solve the exact minimum-cost permutation for small batches.
5. Use row and column sums to confirm marginal preservation.

## Validation

Run:

```bash
python scripts/coupling.py --self-test
python tests/test_coupling.py
```

## Limitations

- `batch_ot` is exhaustive and intended for bounded recovery/tests.
- The script implements square couplings only.
- It preserves the paper mechanism but is not a full high-dimensional training implementation.
