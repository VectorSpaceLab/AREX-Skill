# Troubleshooting — imbalanced-learn

## Install and import issues

- If `import imblearn` fails, first check the environment with `python -m pip
  check` and confirm the editable install is using the target prefix, not a
  different checkout or the user site.
- For a fresh environment, install the package plus the needed extras for the
  selected workflow. Core resampling and evaluation only need the base package;
  DataFrame workflows benefit from `pandas`; balanced mini-batch helpers need
  `tensorflow`/`keras` available at import time.
- `imblearn.keras` may import but still fail to instantiate
  `BalancedBatchGenerator` if Keras/TensorFlow is not installed. That is an
  optional-capability issue, not a core package failure.

## Resampling and data-shape issues

- `SMOTE`/`ADASYN`/`SMOTENC`/`SMOTEN` need enough minority samples and valid
  neighbor settings. If you see a neighbor-related `ValueError`, reduce
  `k_neighbors` or choose a sampler that matches the class counts.
- `SMOTENC` needs categorical feature indices, names, or mask information that
  matches the input layout. For pandas DataFrames, use the actual column names
  or a boolean mask that matches the transformed feature set.
- `RandomOverSampler` with `shrinkage` only applies to numeric data.
- `ClusterCentroids` can accept sparse input, but its generated centroids are
  not inherently sparse-friendly. Expect dense-ish output or inefficiency.
- Many samplers preserve pandas DataFrame output when the input is a DataFrame,
  but object dtypes, categorical columns, or sparse pandas frames may need extra
  care.
- If a custom sampler does not define the expected attributes or returns an
  unexpected pair, `FunctionSampler`/`BalancedBatchGenerator` workflows may fail.

## Pipeline and model-selection issues

- `Pipeline.fit_transform(X, y)` in imbalanced-learn can resample, while
  separate `fit` and `transform` do not. Do not treat it like the scikit-learn
  equivalence relation.
- Resampling the full dataset before splitting causes leakage and overly
  optimistic scores. The correct pattern is split first, resample only the
  training branch, and keep the test set in its natural distribution.
- `InstanceHardnessCV` only supports binary classification and needs an
  estimator that implements `predict_proba`.
- If a model-selection splitter or ensemble complains about `sample_weight`,
  confirm the specific estimator actually supports it. Support varies by class.

## Dataset and metric issues

- `fetch_datasets` downloads benchmark data from Zenodo by default. If offline
  use is required, pass `download_if_missing=False` and expect a failure when
  the cache is empty.
- `make_imbalance` accepts a mapping or callable sampling strategy. If the
  callable returns invalid counts, the underlying under-sampler will raise.
- `classification_report_imbalanced` and `geometric_mean_score` are sensitive
  to label ordering, averaging mode, and the chosen positive label. For binary
  use, verify `pos_label`; for multiclass, choose the appropriate average.
- `ValueDifferenceMetric` is for categorical features. Encode categories before
  calling it on numeric arrays, and make sure the training set actually covers
  the categories you want to compare.

## Optional balanced batch generators

- `balanced_batch_generator` requires the underlying sampler to expose
  `sample_indices_`.
- If `len(generator)` looks smaller than expected, remember that the length is
  computed with floor division by `batch_size`.
- `BalancedBatchGenerator` defaults to dense batches unless `keep_sparse=True`.
- If Keras imports but `BalancedBatchGenerator` still fails, check the active
  backend and whether TensorFlow is the backend provider on this machine.

## Practical recovery checklist

1. Re-run the package smoke script.
2. Re-check the selected sub-skill reference for the exact sampler or workflow.
3. Confirm the input type: NumPy array, sparse matrix, DataFrame, categorical
   columns, or a label vector.
4. Confirm whether the issue is core, optional, or network-bound.
5. If the problem is only a missing optional backend, mark that capability as
   unverified rather than claiming it failed the core package.
