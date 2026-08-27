# Training Troubleshooting

## Common failures

- **`load_weights` does not populate the model the way you expected**
  - Cause: the head shape changed or the layer names no longer match.
  - Fix: load by name and check that the class count and predictor head names match the source weights.

- **The encoder or loss complains about scales, aspect ratios, or variances**
  - Cause: the model builder and the encoder are not using the same anchor configuration.
  - Fix: keep the anchor settings identical on both sides and re-run the smoke script.

- **The training loss becomes `NaN` early**
  - Cause: the optimizer is too aggressive, the data contains degenerate labels, or the model is seeing invalid batches.
  - Fix: reduce the batch size, inspect the labels, and make sure the data-preparation route removed bad boxes.

- **`OOM` during the first iterations**
  - Cause: the input resolution or batch size is too large for the current device.
  - Fix: use a smaller batch size or fall back to the SSD7 smoke path first.

- **`load_model` cannot deserialize a saved SSD model**
  - Cause: the custom layers or custom loss were not passed in `custom_objects`.
  - Fix: include `AnchorBoxes`, `L2Normalization`, `DecodeDetections`, and `compute_loss` when loading.

- **Weight transfer to a new class count fails**
  - Cause: the classifier tensor shapes in the source and target models do not line up.
  - Fix: use `sample_tensors` to adapt the classifier kernels and biases before loading them.

- **The model compiles but the targets do not seem to match the output**
  - Cause: `SSDInputEncoder` was created with the wrong image size or predictor sizes.
  - Fix: get the predictor sizes from the actual model instance and reuse the exact same scales and aspect ratios.

## Fast recovery path

1. Run `scripts/check_env.py`.
2. Run `sub-skills/training/scripts/smoke.py`.
3. Confirm the builder, encoder, and loss all agree on the same anchor configuration.
4. Only then retry the full notebook-scale training recipe.
