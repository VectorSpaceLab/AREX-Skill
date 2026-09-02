---
name: random_layer_mapping
description: Sample and audit RAIL-KD random teacher-to-student intermediate layer mappings for bounded knowledge distillation experiments.
---

# Random Layer Mapping

Use this skill when implementing or checking the RAIL-KD layer-selection mechanism. It is appropriate for transformer distillation or proxy experiments that need to select `m` teacher intermediate layers from an `n`-layer teacher at each epoch and align them with `m` student layers. Do not use it for deterministic PKD/CKD mapping search or attention-over-all-layers methods.

## Inputs

- `teacher_layer_count`: positive integer `n`.
- `student_layer_count`: positive integer `m`, with `m <= n`.
- `seed` and optional `epoch`: reproducibility controls.
- `sort_indices`: keep true for the paper-faithful monotonic alignment.

## Outputs

- A list of distinct zero-based teacher layer indices.
- Student-to-teacher mapping pairs.
- Optional coverage counts over repeated epochs.

## Workflow

1. Validate layer counts before sampling.
2. Use seeded random sampling without replacement to choose exactly `m` teacher layers.
3. Sort the selected teacher layers before pairing with student layers unless a diagnostic explicitly needs unsorted samples.
4. Pair student layers `0..m-1` with the selected teacher indices.
5. For multi-epoch experiments, record mappings and coverage so analysis can verify that randomization was exercised.

## Validation

Run:

```bash
python scripts/rail_mapping.py --teacher-layers 12 --student-layers 6 --epochs 4 --seed 13
python -m pytest tests
```

The tests are standard-library compatible through the Distiller simple test runner.

## Limitations

The script only handles mapping selection and audit statistics. It does not compute hidden-state losses, logits KD, or optimizer updates. Indexing is zero-based; convert explicitly if a downstream framework reports one-based layer numbers.
