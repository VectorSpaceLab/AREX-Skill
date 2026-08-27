# Multivariate Troubleshooting

## 2D-vs-3D confusion

**Symptoms**
- `check_3d_array` rejects the input.
- A wrapped estimator complains about the number of dimensions.

**Likely causes**
- The input is univariate but was routed here.
- The channel axis is missing or collapsed.

**What to do next**
1. Verify the data shape before modeling.
2. Keep the sample, channel, and timestamp axes explicit.
3. Route back to the univariate sub-skills if the data is really 2D.

## Flattening confusion

**Symptoms**
- The wrapped transformer returns a shape that is too nested or too flat.

**Likely causes**
- `flatten=False` was chosen when the downstream estimator wanted tabular
  features.
- `flatten=True` was chosen when you wanted to preserve image-like structure.

**What to do next**
1. Decide whether the downstream estimator expects images or a feature matrix.
2. Keep `flatten=False` for the explicit image path.
3. Flatten only when the next estimator cannot consume higher-rank arrays.

## Empty or tiny WEASELMUSE output

**Symptoms**
- `WEASELMUSE` returns an empty-looking feature matrix on a tiny fixture.

**Likely causes**
- The thresholds are too aggressive for the sample count.
- The fixture is too small for the selected discretization settings.

**What to do next**
- Use a slightly larger multivariate sample when you need a more realistic fit.
- Treat the empty-ish result as a parameter-tuning signal rather than an API
  failure.

## Wrapper compatibility

**Symptoms**
- A univariate estimator does not behave well once wrapped.

**Likely causes**
- The wrapped estimator has its own shape or sparsity assumptions.

**What to do next**
- Test the univariate estimator on one channel first.
- Then wrap it with `MultivariateTransformer` or `MultivariateClassifier`.
