---
name: training-utilities
description: "Assemble safe Segmentation Models training, evaluation,
  fine-tuning, preprocessing, mask-shape, non-RGB, and tiny smoke-test
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Segmentation Models Training Utilities

Use this sub-skill when a task asks how to train, evaluate, fine-tune, smoke-test, or troubleshoot Keras/TensorFlow Keras workflows built with Segmentation Models (`segmentation_models`). The focus is the safe operating loop around an already chosen model architecture/backbone: data/mask conventions, preprocessing, compile/fit/evaluate/predict, encoder freeze/unfreeze, regularization, and tiny synthetic checks.

## Read when

- Assembling a Segmentation Models training pipeline with `sm.get_preprocessing(BACKBONE)`, `sm.Unet`, `sm.Linknet`, `sm.FPN`, or `sm.PSPNet`.
- Deciding `classes` and output `activation` from binary, mutually exclusive multiclass, or overlapping multilabel masks.
- Adapting non-RGB images to Segmentation Models.
- Freezing a pretrained encoder, unfreezing for fine-tuning, or adding regularization to an existing Keras model.
- Running a no-network, no-dataset smoke test before committing to real training.

## Route elsewhere

- Constructor signatures, architecture defaults, backbone catalogs, and PSPNet/FPN shape rules belong to the sibling `model-construction` sub-skill.
- Loss/metric formulas, class weighting math, threshold behavior, and detailed loss object selection belong to the sibling `losses-metrics` sub-skill.
- Package-level installation/import problems belong first to the root skill troubleshooting reference; this sub-skill covers workflow-level symptoms after import.

## Fast operating procedure

1. Set the framework before importing Segmentation Models in modern environments:

   ```python
   import os
   os.environ.setdefault("SM_FRAMEWORK", "tf.keras")
   import segmentation_models as sm
   from tensorflow import keras
   ```

2. Choose a `BACKBONE` and create `preprocess_input = sm.get_preprocessing(BACKBONE)`.
3. Prepare images as batches shaped `(N, H, W, C)` and masks as `(N, H, W, classes)`. Apply backbone preprocessing to images only, never to mask channels.
4. Choose `classes` and final activation:
   - one foreground class: `classes=1`, `activation="sigmoid"`;
   - mutually exclusive foreground classes plus background: `classes=len(CLASSES)+1`, `activation="softmax"`;
   - overlapping multilabel targets: `classes=len(LABELS)`, `activation="sigmoid"`.
5. Build, compile, fit, evaluate, and predict with ordinary Keras APIs. Modern Keras accepts arrays, `keras.utils.Sequence`, and Python generators through `model.fit(...)`; use `fit_generator` only for legacy code you are maintaining.
6. For fine-tuning, pass `encoder_freeze=True` at construction, train the decoder briefly, then call `sm.utils.set_trainable(model, recompile=False)` and explicitly recompile with a suitably small learning rate. Use `recompile=True` only in legacy Keras environments where the model still exposes the compile attributes that Segmentation Models expects.
7. If the user needs confidence that the runtime can train at all, run the bundled smoke script with synthetic arrays:

   ```bash
   python scripts/tiny_training_smoke.py --mode binary --epochs 1 --run-predict
   ```

## Bundled references

- `references/training-workflows.md` — compile/fit/evaluate/predict and fine-tuning recipes.
- `references/data-and-masks.md` — image/mask shapes, class-channel choices, preprocessing, and non-RGB strategies.
- `references/troubleshooting.md` — common workflow failures and fixes.

## Bundled script

- `scripts/tiny_training_smoke.py` — safe synthetic Unet training/evaluation/prediction smoke for `binary`, `multiclass`, and `non-rgb` modes. It uses `encoder_weights=None` and does not download data or pretrained weights.
