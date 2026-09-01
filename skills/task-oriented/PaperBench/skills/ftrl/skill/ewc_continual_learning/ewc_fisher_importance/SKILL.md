---
name: ewc_fisher_importance
description: Estimate and normalize diagonal Fisher importance vectors for Elastic Weight Consolidation from first-order gradients.
---

# EWC Fisher Importance

Use this skill after learning a previous task and before applying an EWC penalty. It converts per-example gradients into a nonnegative diagonal Fisher estimate and can compute normalized Fisher overlap diagnostics.

## Inputs

- Per-example gradient vectors for the previous task.
- Optional Fisher vectors for normalization or overlap.

## Outputs

- Mean squared-gradient Fisher vector.
- Trace-normalized Fisher vector.
- Fisher-overlap score for diagnostics.

## Workflow

1. Collect gradients at or near the previous-task solution.
2. Square every gradient component.
3. Average squared gradients across examples.
4. Normalize by trace only for overlap/comparison diagnostics.
5. Pass the unnormalized Fisher to the EWC penalty.

## Validation

Run:

```bash
python tests/test_fisher_importance.py
```

## Limitations

The helper expects gradient vectors supplied by a model-specific training harness. It does not compute autograd gradients itself.
