# Troubleshooting

## Predictor shape is wrong

**Symptoms**
- `explain` raises a shape error.
- The metric complains about binary vs continuous outputs.

**Likely cause**
- The predictor does not return a batched `numpy.ndarray` with the expected prediction shape.

**Fix**
- Wrap the model with a function that accepts a batch of rows and returns the same batch dimension in the output.
- For classification, use `predict_proba` when the method needs class probabilities.
- For permutation importance with accuracy-like metrics, use class labels rather than probabilities.

## Categorical names or indices are wrong

**Symptoms**
- Plot labels look scrambled.
- The explainer complains about categorical features or grid points.

**Likely cause**
- `feature_names`, `categorical_names`, and the feature matrix do not describe the same columns.

**Fix**
- Confirm the encoded column order before explaining.
- If a feature is categorical, make sure the mapping lines up with the encoded representation used by the predictor.

## Custom grid fails

**Symptoms**
- The grid-related call raises an error or returns strange plots.

**Likely cause**
- Grid points are not monotonic, not numeric, or not compatible with the feature encoding.

**Fix**
- Sort the grid values.
- Use `grid_resolution` first if you only need a coarse plot.
- Use the smoke script to confirm the predictor works before debugging a custom grid.

## Tree-based PD fails

**Symptoms**
- `TreePartialDependence` refuses the model.

**Likely cause**
- The estimator is not one of the supported tree-based predictors.

**Fix**
- Switch back to `PartialDependence` for a black-box predictor.
- Use the tree-specific path only when the estimator is supported.

## Plotting fails

**Symptoms**
- Matplotlib plotting raises an error about feature names or axes.

**Likely cause**
- The explanation was created with mismatched metadata or a feature filter that does not exist.

**Fix**
- Check the feature selection and the labels first.
- Run `scripts/smoke_global_tabular.py` to see the expected output shape.

## Where to go next

- Read `references/workflows.md` to pick the right global tabular method.
- Use the root optional-dependency checker only if the task is actually SHAP or TensorFlow-related.
