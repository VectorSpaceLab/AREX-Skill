# Statistics and Decoding Notes

Read this for cluster statistics, adjacency, regression, and decoding workflows.

## Cluster statistics

Cluster tests are useful when the task has many related comparisons across
sensors, times, frequencies, or source vertices.

Checklist:

1. Put observations on the first axis.
2. Verify the remaining axes match the adjacency you plan to use.
3. Decide one-sided vs two-sided testing (`tail`) and threshold strategy.
4. Use a fixed `seed` for reproducible code examples.
5. Keep exploratory `n_permutations` small for smoke checks, then increase for
   scientific results.
6. Report both cluster-level p-values and the dimensions/time-frequency bins
   each cluster covers.

Adjacency sources:

- Sensor adjacency from channel layouts or `find_ch_adjacency`.
- Time-frequency adjacency from combining channel/frequency/time grids.
- Source adjacency from `spatio_temporal_src_adjacency` or related helpers once
  source spaces are known.

Do not use adjacency from a different channel set, source space, or time grid.

## Regression and multiple comparisons

- Use `mne.stats.linear_regression` when modeling continuous or categorical
  predictors across MNE objects.
- Use FDR/Bonferroni helpers when tests are independent enough and cluster
  assumptions are not desired.
- Keep design matrices and metadata aligned with epochs. Dropped epochs change
  row order; inspect `epochs.selection` and metadata after rejection.

## Decoding without leakage

Leakage-safe decoding keeps all data-dependent transforms inside the
cross-validation estimator:

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from mne.decoding import SlidingEstimator, cross_val_multiscore

clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
time_decod = SlidingEstimator(clf, scoring='roc_auc')
scores = cross_val_multiscore(time_decod, X, y, cv=5)
```

For CSP or Xdawn, put the MNE transformer inside the same pipeline as the final
classifier. Do not fit CSP on all epochs and then cross-validate only the
classifier.

## CSP-specific decisions

- `n_components` controls dimensionality and must be small relative to channels
  and trials.
- `reg` and `rank` affect covariance estimation stability.
- `log` and `transform_into` change feature interpretation.
- `component_order='mutual_info'` is the verified default in the inspected
  package.

## Time-resolved decoding

- `SlidingEstimator` fits or applies an estimator across time points.
- `GeneralizingEstimator` trains at each time point and tests across all time
  points.
- Confirm whether `allow_2d` is appropriate; many MNE decoding workflows expect
  three-dimensional epoched data.

## Optional dependency handling

If importing `mne.decoding.CSP` or scikit-learn pipelines fails with
`ModuleNotFoundError: No module named 'sklearn'`, install a MNE optional/full
set or `scikit-learn` explicitly in the user's environment. Do not add
scikit-learn to a locked production environment without permission.

## Reporting results

- Keep raw scores, mean/SEM, cross-validation splits, scorer, and random seeds.
- Plotting score time courses or topographies routes to `visualization-reporting`.
- For statistical claims, include sample size, number of permutations, cluster
  threshold, correction method, and exact observations axis.
