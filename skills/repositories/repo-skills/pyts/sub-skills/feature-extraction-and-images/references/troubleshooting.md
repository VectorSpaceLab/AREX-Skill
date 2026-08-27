# Feature / Image / SSA Troubleshooting

## `ROCKET` kernel-size errors

**Symptoms**
- `ROCKET` raises an error that a kernel size is larger than the number of
  timestamps.

**Likely causes**
- The default kernel sizes `(7, 9, 11)` are too large for a tiny smoke array.

**What to do next**
1. Shrink the kernel sizes, for example to `(3, 5, 7)`.
2. Use a longer time series when you want the defaults.
3. Keep the smoke case tiny and deterministic.

## `ShapeletTransform` runtime cost

**Symptoms**
- The transform is slow even on small data.
- The fit step takes noticeably longer than the rest of the smoke script.

**Likely causes**
- Shapelet search is expensive by design.
- `n_shapelets` or the search space is too large for a quick smoke.

**What to do next**
1. Use a tiny fixture and a fixed `random_state`.
2. Keep the smoke helper at `n_shapelets=1`.
3. If you need real coverage, run the selected native tests instead of growing
   the smoke input.

## `WEASEL` empty or tiny outputs

**Symptoms**
- `WEASEL` returns a matrix with zero columns or otherwise tiny output.

**Likely causes**
- `word_size`, `window_sizes`, `drop_sum`, `strategy`, or `chi2_threshold`
  are too aggressive for the tiny test data.

**What to do next**
1. Relax the thresholds or use a more realistic training set.
2. Keep `drop_sum=False` when you only want a smoke check.
3. Do not treat an empty matrix on a toy input as a full failure of the package.

## Image flattening confusion

**Symptoms**
- You expected a 2D feature matrix but got image-like arrays instead.

**Likely causes**
- `flatten=False` is keeping the image axes explicit.

**What to do next**
1. Decide whether the downstream estimator wants images or flattened features.
2. Set `flatten=True` only when the downstream model needs a 2D matrix.
3. Use the smoke script's image outputs as a quick reference for the expected
   shapes.

## SSA shape confusion

**Symptoms**
- The output shape from SSA does not look like a standard feature matrix.

**Likely causes**
- SSA returns component series, not a generic tabular feature array.

**What to do next**
- Treat SSA as a decomposition step before downstream processing.
- Inspect the third axis of the output rather than flattening blindly.
