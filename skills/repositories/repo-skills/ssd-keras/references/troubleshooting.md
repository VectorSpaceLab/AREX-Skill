# Cross-Cutting Troubleshooting

This repository predates the modern Keras / TensorFlow split, so the most common failures are version mismatches, custom-object loading mistakes, and configuration mismatches between the model builder and the data encoder or decoder.

## Environment and backend issues

- **`ImportError` for `keras.engine.topology` or similar Keras internals**
  - Likely cause: Keras 3 or another modern backend stack.
  - Fix: use a Keras 2.x / TensorFlow 1.15-compatible environment.

- **TensorFlow import fails with a protobuf descriptor error**
  - Likely cause: protobuf is too new for TensorFlow 1.15.
  - Fix: downgrade protobuf to `3.20.x` or lower.

- **`Theano` or `CNTK` backend requests fail**
  - Likely cause: those backends are not supported by this repository.
  - Fix: use TensorFlow.

- **`scipy.misc.imread` is missing**
  - Likely cause: modern SciPy removed that legacy helper.
  - Fix: use `imageio.imread` or Pillow in new helper scripts.

- **`np.bool`-style deprecation warnings or errors**
  - Likely cause: NumPy is too new for this 2018 codebase.
  - Fix: stay near the verified NumPy baseline.

## Model configuration issues

- **`ValueError` about missing scales or aspect ratios**
  - Likely cause: the builder and the encoder were not configured with the same anchor-box settings.
  - Fix: match `scales`, `aspect_ratios`, `steps`, `offsets`, `coords`, and `normalize_coords` across all components.

- **`ValueError` about variances**
  - Likely cause: the variance list is missing an entry or contains non-positive values.
  - Fix: use exactly four positive variance values.

- **`decode_detections` asks for image dimensions**
  - Likely cause: `normalize_coords=True` without `img_height` and `img_width`.
  - Fix: pass the image size or disable normalization in the decoder.

- **`load_model` fails for saved SSD models**
  - Likely cause: the custom layers were not passed in `custom_objects`.
  - Fix: include `AnchorBoxes`, `L2Normalization`, `DecodeDetections`, and `compute_loss` as needed.

## Data and label issues

- **Empty batches or removed images**
  - Likely cause: `keep_images_without_gt=False`, degenerate boxes, or too-strict validity filters.
  - Fix: inspect the labels and relax the filter only when appropriate.

- **Boxes vanish after augmentation**
  - Likely cause: the crop, flip, scale, or validator settings are too aggressive for the dataset.
  - Fix: start from the simpler resize-only path and tighten the chain gradually.

- **Class IDs look off by one**
  - Likely cause: background handling differs between the dataset format and the model.
  - Fix: keep background as class 0 in the model-side conventions and make sure the parser maps the dataset classes correctly.

## Verification strategy

When a failure is unclear, the safest recovery is:

1. Run `scripts/check_env.py`.
2. Re-open `references/compatibility.md`.
3. Test the smallest relevant smoke script before retrying the full workflow.

If the smoke script fails, fix the environment or the data contract before moving to the bigger workflow.
