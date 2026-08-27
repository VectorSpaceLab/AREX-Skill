# Metrics and Evaluation Troubleshooting

## Shape or normalization mismatch

- CAM arrays should align with the input spatial shape before they are passed to
  metric helpers.
- If a metric expects one CAM per batch item, keep batch size aligned across the
  input tensor, CAM array, and target list.
- `show_cam_on_image` and some metric helpers expect normalized inputs in a
  specific range; do not feed raw uint8 arrays unless the helper documents that.

## ROAD or confidence metrics are slow

- These metrics call the model again on perturbed inputs. Use a tiny batch and
  a tiny synthetic model first.
- `ROAD` uses sparse imputation and `scipy`; install those runtime dependencies
  before running a real evaluation.
- Keep percentiles narrow while debugging; use averages only after the basic
  path works.

## RefineCAM output looks wrong

- Confirm the target layers are ordered from deeper to shallower or vice versa
  in a sensible way for the model.
- If the result is all zeros, check that each base CAM produces non-zero output
  before multiplication.
- Preserve the `targets` list so each batch member receives the intended scalar.

## DFF issues

- `n_components` must not exceed the rank implied by the activation tensor.
- `scikit-learn` is required for NMF; `numpy` and `torch` are not enough.
- If a concept map looks noisy, inspect whether the activations contained NaNs
  before the factorization.
