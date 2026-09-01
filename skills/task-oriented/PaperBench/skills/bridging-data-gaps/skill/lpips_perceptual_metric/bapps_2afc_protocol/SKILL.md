---
name: bapps_2afc_protocol
description: Evaluate BAPPS-style two-alternative forced choice perceptual similarity triplets with auditable per-item predictions.
---

# BAPPS 2AFC Protocol

Use this skill when evaluating a perceptual distance function on reference, `p0`, `p1`, and human-choice triplets.

Do not use this skill to compute LPIPS distances internally; it owns the protocol and scoring contract only.

## Inputs

- Triplets with `id`, `ref`, `p0`, `p1`, and `judge` fields.
- A distance provider that returns `d0 = distance(ref, p0)` and `d1 = distance(ref, p1)`, or precomputed `d0` and `d1` values.
- Labels where `judge = 0` means `p0` is closer and `judge = 1` means `p1` is closer.

## Outputs

- Aggregate `2afc_accuracy`.
- Per-item predictions, distances, labels, and correctness.

## Workflow

1. Validate every triplet label.
2. Compute or consume `d0` and `d1`.
3. Predict `1` when `d1 < d0`; otherwise predict `0`.
4. Average correctness over items.
5. Save per-item records for recovery analysis.

## Validation

Run:

```bash
python scripts/evaluate_2afc.py --self-test
python tests/test_evaluate_2afc.py
```

## Limitations

Ties default to prediction `0` for deterministic scoring. If a benchmark specifies probabilistic tie handling, record that deviation outside this skill.
