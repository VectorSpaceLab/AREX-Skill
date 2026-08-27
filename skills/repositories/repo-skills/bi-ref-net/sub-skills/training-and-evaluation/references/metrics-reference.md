# Metrics reference

## Evaluator contract

Signature:

```python
evaluation.metrics.evaluator(
    gt_paths,
    pred_paths,
    metrics=['S', 'MAE', 'E', 'F', 'WF', 'MBA', 'BIoU', 'MSE', 'HCE'],
    verbose=False,
    num_workers=8,
)
```

Behavior:

- `gt_paths` and `pred_paths` must be lists of the same length.
- The evaluator reads grayscale images, resizes each prediction to the GT size, and skips missing or unreadable files.
- When the pair count is large enough and `num_workers > 1`, it uses parallel loading; tiny smoke fixtures stay on the serial path.
- For HCE, the evaluator can create `ske/` files from GT masks if no skeleton file already exists.

Return value order:

```python
(em, sm, fm, mae, mse, wfm, hce, mba, biou)
```

Where:

- `em`, `fm`, and `biou` are dictionaries with curves.
- the others are scalar values.

## Metric meanings

| Flag | Meaning | Typical return shape | Notes |
|---|---|---|---|
| `S` | S-measure | scalar float | Usually the headline segmentation score. |
| `MAE` | Mean absolute error | scalar float | Lower is better. |
| `E` | Enhanced alignment measure | `{'adp', 'curve'}` | `curve` is a 256-step array. |
| `F` | F-measure | `{'adp', 'curve'}` | `curve` is a 256-step array. |
| `WF` | Weighted F-measure | scalar float | Used heavily in the repo's tables. |
| `MBA` | Boundary accuracy | scalar float | Boundary-focused metric. |
| `BIoU` | Boundary IoU | `{'curve'}` | `curve` is a 256-step array. |
| `MSE` | Mean squared error | scalar float | Mainly appears in matting tables. |
| `HCE` | Human correction effort | scalar value | DIS-only in the display helpers. |

## How the pretty table is assembled

`sort_and_round_scores(task, scores, r=3)` reorders the evaluator tuple into the display order used by `eval_existingOnes.py`.

The input must be the tuple listed above in the exact order returned by `evaluator`.

### Task-specific display order

| Task | Display order |
|---|---|
| `DIS5K` | `maxFm, wFmeasure, MAE, Smeasure, meanEm, HCE, maxEm, meanFm, adpEm, adpFm, mBA, maxBIoU, meanBIoU` |
| `COD` | `Smeasure, wFmeasure, meanFm, meanEm, maxEm, MAE, maxFm, adpEm, adpFm, HCE, mBA, maxBIoU, meanBIoU` |
| `HRSOD` | `Smeasure, maxFm, meanEm, MAE, maxEm, meanFm, wFmeasure, adpEm, adpFm, HCE, mBA, maxBIoU, meanBIoU` |
| `General` | `maxFm, wFmeasure, MAE, Smeasure, meanEm, HCE, maxEm, meanFm, adpEm, adpFm, mBA, maxBIoU, meanBIoU` |
| `General-2K` | `maxFm, wFmeasure, MAE, Smeasure, meanEm, HCE, maxEm, meanFm, adpEm, adpFm, mBA, maxBIoU, meanBIoU` |
| `Matting` | `Smeasure, maxFm, meanEm, MSE, maxEm, meanFm, wFmeasure, adpEm, adpFm, HCE, mBA, maxBIoU, meanBIoU` |
| fallback | `Smeasure, MAE, maxEm, meanEm, maxFm, meanFm, wFmeasure, adpEm, adpFm, HCE, mBA, maxBIoU, meanBIoU` |

## Output conventions

- `eval_existingOnes.py` rounds most values to 3 decimals when formatting tables.
- `HCE` is rounded to an integer-like value in the tables.
- `MSE` uses a 5-decimal display in the matting table.
- When a metric is not requested, the evaluator returns a placeholder such as `-1` or a dictionary containing `curve=[-1]`.

## Smoke-test guidance

For a quick bounded check, run the bundled metric smoke script with an explicit repository root. Use `--metrics all` to exercise the full evaluator or a smaller subset such as `S+MAE+WF` for a quicker sanity check.
