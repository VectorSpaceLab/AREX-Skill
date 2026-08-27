---
name: model-construction
description: "Construct Keras segmentation models with Segmentation Models
  architectures, backbones, preprocessing, and input validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Construction

Use this sub-skill when a task asks how to instantiate or diagnose Segmentation Models Keras models: choosing an architecture, selecting a backbone, configuring `input_shape`, `classes`, `activation`, `encoder_weights`, `encoder_freeze`, preprocessing, and constructor-specific validation.

Do not use this sub-skill for loss/metric math or full training loops. Route losses and metrics to `losses-metrics`; route optimizer/fit utilities, `set_trainable`, and `set_regularization` to `training-utilities`.

## Operating checklist

1. **Select the framework before import.** In modern TensorFlow environments prefer TensorFlow Keras:

   ```python
   import os
   os.environ["SM_FRAMEWORK"] = "tf.keras"  # or "keras"
   import segmentation_models as sm
   ```

   `sm.set_framework("tf.keras")` and `sm.set_framework("keras")` exist, but objects should be created only after the intended framework has been selected.

2. **Choose task outputs.** For binary segmentation use `classes=1, activation="sigmoid"`. For mutually exclusive multiclass segmentation use a channel per class (often classes plus background) with `activation="softmax"`. For independent multi-label masks use multiple channels with `activation="sigmoid"`.

3. **Choose architecture/backbone.** See `references/backbones-and-architectures.md` for the supported names and selection guidance.

4. **Configure preprocessing by backbone.** Use `preprocess_input = sm.get_preprocessing(backbone_name)` and apply it to image tensors produced for the same backbone.

5. **Choose input shape safely.** `Unet`, `Linknet`, and `FPN` can use dynamic spatial dimensions such as `(None, None, 3)`, but actual image height/width should normally be divisible by 32. `PSPNet` requires concrete height/width divisible by `6 * downsample_factor`.

6. **Avoid accidental network downloads.** `encoder_weights="imagenet"` may download pretrained encoder weights and expects RGB-compatible input. For smoke tests, offline builds, grayscale, multispectral, or arbitrary channel counts, use `encoder_weights=None` or map non-RGB inputs to 3 channels before the model.

7. **Smoke-check unusual configs.** Use `scripts/model_constructor_smoke.py` for a safe constructor check; it defaults to `encoder_weights=None` and does not run prediction unless `--predict` is passed.

## Key references

- `references/api-reference.md` — constructor signatures, defaults, framework and preprocessing examples.
- `references/backbones-and-architectures.md` — architecture/backbone trade-offs and supported names.
- `references/troubleshooting.md` — common constructor/import/shape failures and recoveries.
- `scripts/model_constructor_smoke.py` — CLI smoke script for offline model-construction checks.
