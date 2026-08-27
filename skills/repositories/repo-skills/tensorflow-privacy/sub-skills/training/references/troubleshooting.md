# Training troubleshooting

## Loss shape or reduction problems

### Symptom
- The DP optimizer raises a shape error, reduction error, or a complaint about per-example gradients.

### Likely cause
- The loss was reduced to a scalar before the DP wrapper saw it.
- A Keras loss was compiled with the default reduction instead of per-example reduction.

### Recovery
- Use a loss configured with `reduction=NONE` for the DP optimizer path.
- Re-check the tiny training smoke helper and make sure the batch size matches the microbatching plan.

## `apply_gradients` assertion

### Symptom
- The optimizer complains that DP gradients were not produced.

### Likely cause
- The optimizer was used like a plain optimizer, or the custom loop bypassed the DP gradient path.

### Recovery
- Make sure the training step routes through the DP optimizer's own gradient computation.
- Confirm that the model is not silently using a non-DP optimizer.

## `num_microbatches` problems

### Symptom
- Errors about mismatched batch size, microbatch count, or unsupported sparse gradients.

### Likely cause
- `num_microbatches` does not align with the batch structure.
- Sparse gradients are used with large-batch emulation.

### Recovery
- Reduce the example to a tiny smoke fixture and pick a microbatch count that divides the batch cleanly.
- Avoid large-batch emulation for sparse-gradient paths unless the code path explicitly supports it.

## Estimator import errors

### Symptom
- `tensorflow_estimator` cannot be imported when using `DNNClassifier`.

### Likely cause
- The TensorFlow Estimator package is missing from the environment.

### Recovery
- Install the repo's runtime requirements again, then re-run the bundled environment checker.

## Sparse / vectorized variants

### Symptom
- A sparse or vectorized optimizer behaves differently from the plain Keras variant.

### Likely cause
- The model uses layer types or loss reductions that do not match the variant's assumptions.

### Recovery
- Start with the plain Keras DP optimizer first, then move to the vectorized or sparse variant only after the tiny smoke helper works.

## `DPModel` and fast-clipping cross-over

### Symptom
- `DPModel` works on one model but fails on a model with custom layers.

### Likely cause
- The layer registry does not cover the model's trainable layers.

### Recovery
- Read the fast-clipping sub-skill and add the missing registry support, or stay on the plain DP optimizer path.
