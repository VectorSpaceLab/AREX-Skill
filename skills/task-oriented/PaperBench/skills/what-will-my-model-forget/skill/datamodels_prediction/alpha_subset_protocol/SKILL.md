---
name: alpha_subset_protocol
description: Generate and validate fixed-cardinality alpha-subset membership matrices for datamodel training and recovery experiments.
---

# Alpha-Subset Protocol

Use this skill when a datamodel experiment needs membership vectors sampled from an alpha-fraction subset distribution. Do not use it for variable-size bootstrap subsets unless the caller explicitly declares a different subset distribution.

## Inputs

- Base training-set size `d`.
- Subsampling fraction `alpha` in `(0, 1]`.
- Number of subsets `num_subsets`.
- Integer random seed.

## Outputs

- Binary membership matrix as JSON or a Python list of lists.
- Metadata with `d`, `alpha`, `subset_size`, `num_subsets`, and `seed`.

## Workflow

1. Validate dimensions and alpha.
2. Compute `subset_size = max(1, round(alpha * d))`.
3. Sample each subset without replacement using a deterministic local RNG.
4. Validate that every row is binary and has the exact subset size.
5. Pass both matrix and metadata to datamodel fitting.

## Validation

Run:

```bash
python scripts/subset_protocol.py --d 8 --alpha 0.5 --num-subsets 4 --seed 3
python tests/test_subset_protocol.py
```

## Limitations

This skill samples membership only. It does not train base models or compute target outcomes.
