# Analytics reference

This reference covers the direct Python preprocessing, statistics, and ML
APIs used for tabular and classical model workflows.

## Preprocessing and metrics

| API | Purpose | Notes |
| --- | --- | --- |
| `secretflow.preprocessing.StandardScaler` | Federated scaling | Works on `HDataFrame`, `VDataFrame`, or `MixDataFrame` inputs |
| `secretflow.stats.psi_eval` | PSI-style score calculation | Accepts `FedNdarray` or `VDataFrame` inputs |
| `secretflow.stats.table_statistics` | Tabular summary statistics | Useful for quick dataset inspection |
| `secretflow.stats.categorical_statistics` | Categorical summaries | Good for discrete columns and feature audits |
| `secretflow.stats.ScoreCard` | Score-card style transformations | Common in risk-control style workflows |

## Classical ML catalog

| Module / class | Use when | Common runtime shape |
| --- | --- | --- |
| `secretflow.ml.linear.SSGLM` | GLM-style fitting and prediction | SPU-backed linear model |
| `secretflow.ml.linear.SSRegression` | Regression-style training | SPU-backed linear model |
| `secretflow.ml.linear.FlLogisticRegressionMix` | Federated logistic regression with mixed partitions | Direct Python workflow |
| `secretflow.ml.linear.FlLogisticRegressionVertical` | Federated logistic regression on vertical data | Uses devices, aggregator, and HEU |
| `secretflow.ml.linear.HESSLogisticRegression` | HESS logistic regression | Requires SPU and HEU devices |
| `secretflow.ml.cluster.kmeans.KMeans` | K-means clustering | SPU-backed |
| `secretflow.ml.naive_bayes.gnb.GNB` | Gaussian Naive Bayes | SPU-backed |
| `secretflow.ml.gaussian_process.gaussian_process_classifier.GPC` | Gaussian-process classification | SPU-backed |
| `secretflow.ml.neighbors.knn.KNNClassifer` | Nearest-neighbor classification | SPU-backed |

## Typical workflow choices

### Preprocessing
1. Build the federated dataframe first.
2. Choose the scaler or transformation that matches the dataframe shape.
3. Fit on the federated structure, then reveal only the final transformed data
   you actually need to inspect.

### Statistics
1. Make sure the data is already partitioned in the shape the metric expects.
2. Choose the summary or PSI helper.
3. Compare the output against a small known fixture or an equivalent
   single-party baseline when possible.

### ML models
1. Start with the direct class constructor and a clear SPU or device layout.
2. Keep the sample size small for smoke tests and notebook examples.
3. If the task later needs export or a serving package, move to the component
   route rather than forcing the direct class to do both jobs.

## Input expectations

- Many of the direct ML classes assume a secure compute device, not just plain
  Python arrays.
- The federated table helpers assume the owning parties are already clear.
- Some workflows use plain aggregators and comparators to align or reconcile
  the data before fitting.

## Troubleshooting

### Missing optional dependencies
Some examples and tests rely on extra packages such as `xgboost` or
`statsmodels`. Add them only when the selected workflow needs that path.

### SPU / HEU layout errors
If a model complains about the device layout, verify the SPU cluster definition,
party names, and any HEU devices before looking at the estimator code.

### Convergence or fit issues
- Start with tiny fixtures.
- Check that the labels and feature partitions line up.
- Compare the result against a plain scikit-learn baseline when the workflow is
  expected to match a familiar estimator family.

### PSI / score mismatches
Use the smallest possible split-point or binning fixture first. If the numbers
still disagree, confirm the dataframe or array shape before changing the model
logic.

## Cross-links

- Root troubleshooting: `../../references/troubleshooting.md`
- Smoke helper: `../scripts/analytics_smoke.py`
