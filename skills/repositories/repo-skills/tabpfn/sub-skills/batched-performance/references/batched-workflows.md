# Batched Inference Workflows

## Classifier workflow

`TabPFNClassifier.predict_proba_batched(X_train_list, y_train_list, X_test_list)`
combines many datasets into one fused batched forward pass per estimator.

Requirements:

- All three lists must have equal length and non-zero length.
- Every dataset must share the same set of classes.
- All training arrays must share one shape.
- All test arrays must share one shape.

The return value has shape `(n_datasets, n_test, n_classes)`.

### Good use cases

- Cross-validation folds.
- Grouped datasets that are identical in shape.
- Repeated evaluations where preprocessing cost dominates.

## Regressor workflow

`TabPFNRegressor.predict_batched(X_train_list, y_train_list, X_test_list, output_type=...)`
works similarly, but each dataset may have its own target scale.

The return value is one prediction object per dataset in input order. Supported
`output_type` values are the same as ordinary `predict`.

### Good use cases

- Multiple independent regression problems with matching shapes.
- Repeated benchmarking on the same checkpoint.
- Batched quantile or distribution analysis.

## What batched prediction does internally

- Clones the estimator so the original object is not mutated.
- Fits each dataset on the clone.
- Reuses the fitted preprocessors and model weights across the fused batch.
- Runs one estimator at a time through the fused forward path.

## What batched prediction does not do

- It does not pad ragged inputs.
- It does not merge datasets with different class sets.
- It does not replace ordinary `fit`/`predict` for a single dataset.
