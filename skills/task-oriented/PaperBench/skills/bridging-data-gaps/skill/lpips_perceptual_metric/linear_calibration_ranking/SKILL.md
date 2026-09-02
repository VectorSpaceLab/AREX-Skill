---
name: linear_calibration_ranking
description: Fit non-negative layer calibration weights for LPIPS-style distances using bounded 2AFC ranking feedback.
---

# Linear Calibration Ranking

Use this skill when a recovery or evaluation needs to apply or fit the LPIPS paper's shallow human-judgment calibration over per-layer distances.

Do not use it to train or fine-tune a trunk network. This skill updates only calibration weights.

## Inputs

- Items with `layers0`, `layers1`, and `judge`.
- `layers0` and `layers1` are equal-length lists of per-layer distances for `ref-p0` and `ref-p1`.
- `judge = 0` means `p0` should score closer; `judge = 1` means `p1` should score closer.
- Optional initial weights, step count, and learning rate.

## Outputs

- Non-negative calibrated weights.
- Loss/accuracy before and after calibration.
- `params_before` and `params_after` for recovery validation.

## Workflow

1. Validate layer vectors and labels.
2. Score each candidate by weighted layer-distance sum.
3. Compute logistic ranking loss over `score0 - score1`.
4. Run bounded gradient steps on calibration weights.
5. Project weights to non-negative values after each step.
6. Emit a trace with before/after loss, accuracy, and weights.

## Validation

Run:

```bash
python scripts/calibrate_ranking.py --self-test
python tests/test_calibrate_ranking.py
```

## Limitations

The script is intentionally small and deterministic. It is suitable for reduced recovery and unit tests, not full-scale LPIPS training.
