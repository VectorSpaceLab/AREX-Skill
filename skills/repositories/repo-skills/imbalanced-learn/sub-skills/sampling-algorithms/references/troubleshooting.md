# Troubleshooting — sampling algorithms

## Neighbor and cardinality problems

- If a SMOTE-family sampler raises a neighbor-related error, the minority class
  may be too small for the requested `k_neighbors` or `m_neighbors` setting.
- Lower the neighbor count, simplify the data, or choose a non-neighbor-based
  sampler such as `RandomOverSampler` or `RandomUnderSampler`.

## Categorical data problems

- `SMOTENC` needs categorical features to be identified correctly.
- `SMOTEN` is for categorical-only input; it is not a fallback for mixed data.
- If your pandas DataFrame columns are being renamed or converted unexpectedly,
  inspect the column ordering before and after resampling.

## Sparse and dense output surprises

- Several samplers accept sparse inputs but may return dense or partially dense
  outputs.
- `ClusterCentroids` can be especially unfriendly to sparse workflows because
  the generated centroids are not naturally sparse.

## `sampling_strategy` mistakes

- Dict strategies must specify valid target counts.
- Callable strategies must return a valid mapping from class labels to counts.
- A strategy that over-requests samples beyond what the current class supports
  can fail before any resampling happens.

## `FunctionSampler` mistakes

- The callable must return `(X_resampled, y_resampled)`.
- When `validate=True`, the sampler will reject unexpected input shapes or
  target forms.
- If you need a very custom workflow, keep the callable tiny and testable rather
  than burying large preprocessing pipelines inside it.

## Recovery steps

1. Check the class counts before resampling.
2. Inspect the sampler constructor signature in `references/api-reference.md`.
3. Try the nearest simpler family first.
4. Re-run `scripts/sampler_smoke.py`.
