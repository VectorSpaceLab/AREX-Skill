---
name: losses-metrics
description: "Choose, configure, and validate Segmentation Models losses and
  metrics for Keras compile and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Segmentation Models losses and metrics

Use this sub-skill when a task needs to select, configure, debug, or sanity-check `segmentation_models` losses and metrics for Keras / TensorFlow Keras `compile`, `evaluate`, or deterministic tensor checks.

## Route here for

- Binary segmentation metrics such as `IOUScore(threshold=0.5)` and `FScore(threshold=0.5)`.
- Multiclass or multilabel choices among Jaccard, Dice, cross-entropy, and focal losses.
- `class_indexes`, `class_weights`, `threshold`, `per_image`, `smooth`, `beta`, `alpha`, and `gamma` behavior.
- Loss aliases and combinations such as `bce_jaccard_loss`, `categorical_focal_dice_loss`, or custom sums like `DiceLoss(...) + 0.5 * BinaryFocalLoss(...)`.
- Reproducible hand checks for IoU/F-score/precision/recall/Dice/Jaccard math.

## Route elsewhere

- Model constructors, encoder/backbone selection, `Unet`, `Linknet`, `FPN`, or `PSPNet` architecture details: use the model-construction sub-skill.
- Full data loaders, generators, augmentation, preprocessing pipelines, fitting loops, checkpointing, or plotting: use the training-utilities sub-skill.

## Operating prerequisites

In modern environments, prefer TensorFlow Keras and initialize Segmentation Models before constructing loss or metric objects:

```python
import os
os.environ.setdefault("SM_FRAMEWORK", "tf.keras")  # set before importing segmentation_models
import segmentation_models as sm
```

The package constructs `KerasObject`-based aliases at import time and injects Keras backend/layers/models/utils submodules during framework initialization. If these submodules are missing, loss and metric construction fails before model training begins.

## What to read

- `references/api-reference.md` — class signatures, aliases, formulas, and exact parameter semantics.
- `references/recipes.md` — binary, multiclass, multilabel, class-imbalance, and ignored-background compile recipes.
- `references/troubleshooting.md` — common shape, threshold, class-weight, activation/loss, smooth, and framework errors.

## Bundled check

Run the bundled smoke check in the target environment when a task needs deterministic validation without external data:

```bash
python scripts/check_losses_metrics.py --threshold-demo
```

The script builds tiny masks, evaluates the packaged losses/metrics, and prints expected IoU, F-score, precision, recall, loss, class-index, and optional threshold signals.
