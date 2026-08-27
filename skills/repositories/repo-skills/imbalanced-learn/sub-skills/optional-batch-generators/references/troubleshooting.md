# Troubleshooting — optional batch generators

## Missing backend imports

- If `from imblearn.keras import BalancedBatchGenerator` fails, check whether
  Keras or TensorFlow is installed in the active environment.
- If TensorFlow imports but later complains about GPU libraries, remember that
  this sub-skill does not require GPU support; CPU-only TensorFlow is fine for
  the balanced-batch helpers.

## Generator construction problems

- The sampler must expose `sample_indices_`; otherwise the generator cannot
  build batches.
- If the output length looks too small, remember that the generator length uses
  floor division by `batch_size`.
- If sparse input gets densified unexpectedly, check `keep_sparse`.

## Recovery steps

1. Re-run `scripts/batch_generator_smoke.py`.
2. Verify that the chosen sampler can finish `fit_resample`.
3. If only the optional backend is missing, document the skip and continue with
   the core package workflows.
