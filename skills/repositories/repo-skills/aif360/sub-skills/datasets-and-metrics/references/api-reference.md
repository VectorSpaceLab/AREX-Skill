# Legacy datasets and metrics API reference

These facts target AIF360 `0.6.1` legacy dataset/metric workflows. Base dataset and metric classes imported in the verified CPU environment. Optional extras were intentionally not installed; optional-dependency branches are marked optional/unverified.

## Dataset constructors

| Class | Constructor shape | Primary use | Notes |
| --- | --- | --- | --- |
| `StructuredDataset` | `StructuredDataset(df, label_names, protected_attribute_names, instance_weights_name=None, scores_names=[], unprivileged_protected_attributes=[], privileged_protected_attributes=[], metadata=None)` | General numeric tabular dataset. | `df` must be numeric and NA-free. If protected values are not supplied, highest numeric value is inferred privileged and all lower observed values are unprivileged. |
| `BinaryLabelDataset` | `BinaryLabelDataset(favorable_label=1.0, unfavorable_label=0.0, **structured_kwargs)` | Binary-label dataset metrics and most legacy mitigation algorithms. | Labels must be one column and contain only the favorable/unfavorable values. Scores default to labels unless `scores_names` is supplied through `StructuredDataset` kwargs. |
| `StandardDataset` | `StandardDataset(df, label_name, favorable_classes, protected_attribute_names, privileged_classes, instance_weights_name='', scores_name='', categorical_features=[], features_to_keep=[], features_to_drop=[], na_values=[], custom_preprocessing=None, metadata=None)` | Convert a domain/raw DataFrame into a binary legacy dataset. | Applies custom preprocessing, drops unrequested columns/NA rows, one-hot encodes categoricals, maps labels, and maps protected values. |
| `RegressionDataset` | `RegressionDataset(df, dep_var_name, protected_attribute_names, privileged_classes, instance_weights_name='', categorical_features=[], na_values=[], custom_preprocessing=None, metadata=None)` | Ranked/regression metrics. | Maps protected attributes and min-max normalizes the dataframe before `StructuredDataset` construction. |

Built-in wrappers exposed by `aif360.datasets`: `AdultDataset`, `GermanDataset`, `CompasDataset`, `BankDataset`, `MEPSDataset19`, `MEPSDataset20`, `MEPSDataset21`, and `LawSchoolGPADataset`. See [data formats](data-formats.md#built-in-legacy-dataset-wrappers) before loading them because raw data may be absent or network/data-use constraints may apply.

## Metric class selection

| Metric class | Constructor | Use when | Common methods |
| --- | --- | --- | --- |
| `BinaryLabelDatasetMetric` | `BinaryLabelDatasetMetric(dataset, unprivileged_groups=None, privileged_groups=None)` | You have one `BinaryLabelDataset` and need dataset bias/selection metrics on true labels. | `num_instances`, `num_positives`, `num_negatives`, `base_rate`, `statistical_parity_difference`, `disparate_impact`, `mean_difference` alias, `consistency`, `smoothed_empirical_differential_fairness`, `rich_subgroup`. |
| `ClassificationMetric` | `ClassificationMetric(dataset, classified_dataset, unprivileged_groups=None, privileged_groups=None)` | You have a true `BinaryLabelDataset` and a predicted `BinaryLabelDataset` with the same features/protected attributes/weights. | Confusion counts and rates, selection-rate fairness metrics, error-rate parity, equal opportunity/equalized odds, average odds, generalized entropy, Theil, coefficient of variation, differential fairness bias amplification. |
| `SampleDistortionMetric` | `SampleDistortionMetric(dataset, distorted_dataset, unprivileged_groups=None, privileged_groups=None)` | You need distances between original and transformed `StructuredDataset` objects. | `euclidean_distance`, `manhattan_distance`, `mahalanobis_distance`, `total_*`, `average_*`, `maximum_*`. Compute group differences/ratios manually from `average_*_distance(privileged=False/True)` for reliability. |
| `RegressionDatasetMetric` | `RegressionDatasetMetric(dataset, unprivileged_groups=None, privileged_groups=None)` | You need ranking/regression fairness metrics over a `RegressionDataset`. | `infeasible_index(target_prop, r=None)`, `discounted_cum_gain(r=None, full_dataset=None, normalized=False)`. |
| `MDSSClassificationMetric` | `MDSSClassificationMetric(dataset, classified_dataset, scoring='Bernoulli', unprivileged_groups=None, privileged_groups=None, **kwargs)` | You already have a true/predicted dataset pair and want a bias score for a prespecified privileged or unprivileged group. | `score_groups(privileged=True, penalty=1e-17)`. For full subgroup search, route to the detectors sub-skill. |

All group-aware metrics use the same `DatasetMetric` semantics: `metric_fun(privileged=None)` means all rows, `privileged=True` means `privileged_groups`, and `privileged=False` means `unprivileged_groups`. Calling group-conditioned metrics without initializing the corresponding groups raises an attribute error.

## `BinaryLabelDatasetMetric` method groups

Use this class before fitting a classifier or mitigation algorithm, or to describe label imbalance in a dataset.

- **Counts**: `num_instances`, `num_positives`, `num_negatives` support optional group conditioning.
- **Base rates**: `base_rate(privileged=None)` computes `Pr(Y=favorable)` overall or by group.
- **Group parity**: `statistical_parity_difference()` is unprivileged minus privileged base rate; `disparate_impact()` is unprivileged divided by privileged base rate.
- **Individual/distributional helpers**: `consistency(n_neighbors=5)` uses nearest neighbors on features; `smoothed_empirical_differential_fairness(concentration=1.0)` uses smoothed base rates across intersecting protected groups.
- **Rich subgroup**: `rich_subgroup(predictions, fairness_def='FP')` audits rich subgroups for GerryFair-style false-positive or false-negative definitions. If the task is about subgroup discovery rather than metrics, route to detectors/mitigation guidance.

## `ClassificationMetric` method groups

Use this class after you have predictions. The first dataset is ground truth; the second is predictions.

- **Hard confusion counts**: `binary_confusion_matrix`, `num_true_positives`, `num_false_positives`, `num_true_negatives`, `num_false_negatives`.
- **Generalized confusion counts from scores**: `generalized_binary_confusion_matrix`, `num_generalized_true_positives`, `num_generalized_false_positives`, `num_generalized_true_negatives`, `num_generalized_false_negatives`.
- **Performance measures**: `performance_measures`, `true_positive_rate`, `true_negative_rate`, `false_positive_rate`, `false_negative_rate`, `positive_predictive_value`, `negative_predictive_value`, `false_discovery_rate`, `false_omission_rate`, `accuracy`, `error_rate`, plus aliases `precision`, `recall`, `sensitivity`, `specificity`.
- **Group differences/ratios**: `true_positive_rate_difference`, `false_positive_rate_difference`, `false_negative_rate_difference`, `false_positive_rate_ratio`, `false_negative_rate_ratio`, `error_rate_difference`, `error_rate_ratio`, and related omission/discovery-rate variants.
- **Fairness summaries**: `selection_rate`, `statistical_parity_difference`, `disparate_impact`, `average_odds_difference`, `average_abs_odds_difference`, `average_predictive_value_difference`, `equal_opportunity_difference`, `equalized_odds_difference`, `generalized_equalized_odds_difference`.
- **Distributional metrics**: `generalized_entropy_index(alpha=2)`, `theil_index()`, `coefficient_of_variation()`, `between_group_generalized_entropy_index`, `between_all_groups_generalized_entropy_index`, and corresponding Theil/coefficient variants.
- **Differential fairness**: `differential_fairness_bias_amplification(concentration=1.0)` compares smoothed empirical differential fairness of predictions to the original labels.

## `SampleDistortionMetric` caveats

`SampleDistortionMetric` compares two `StructuredDataset` instances. Validation allows differences in `features`, `labels`, and `scores` only; instance order, weights, protected attributes, and metadata-compatible structure must match.

Distance methods return per-sample vectors unless you call an aggregate method:

```python
sdm.average_manhattan_distance()
sdm.average_manhattan_distance(privileged=False)
sdm.average_manhattan_distance(privileged=True)
```

For group parity of sample distortion, compute differences and ratios manually:

```python
unpriv = sdm.average_manhattan_distance(privileged=False)
priv = sdm.average_manhattan_distance(privileged=True)
diff = unpriv - priv
ratio = unpriv / priv
```

Prefer Euclidean or Manhattan distance for tiny or collinear data. Mahalanobis distance inverts a covariance matrix and can fail on singular data.

## `RegressionDatasetMetric` notes

`RegressionDatasetMetric` uses a `RegressionDataset` whose `scores` reflect the normalized dependent variable unless explicit scores are provided through the underlying structured fields.

- `infeasible_index(target_prop, r=None)` requires `target_prop` keys for every observed protected attribute value. With binary mapped protected attributes this usually means both `0.0` and `1.0`.
- `discounted_cum_gain(r=None, full_dataset=None, normalized=False)` computes DCG over the current dataset order. If `normalized=True`, provide `full_dataset` so the ideal DCG denominator can be computed.

## `MDSSClassificationMetric` notes

`MDSSClassificationMetric` extends `ClassificationMetric` and scores prespecified protected groups. It builds coordinates from the dataset features, outcomes from true labels, and expectations from `classified_dataset.scores`.

- `scoring='Bernoulli'` is the parametric default.
- `scoring='BerkJones'` is accepted as a non-parametric option.
- Passing a custom scoring function requires the corresponding MDSS scoring object to be importable.
- `score_groups(privileged=True)` scans in the negative direction for privileged groups; `privileged=False` scans in the positive direction for unprivileged groups.
- For discovering the highest-scoring arbitrary subgroup from a pandas feature matrix, use the detectors sub-skill instead of this metric wrapper.

## Optional OT metric caveat

Optimal-transport distance is optional and **unverified in the base CPU environment** for this generated skill. It requires the `OptimalTransport` extra, which installs the Python Optimal Transport package imported as `ot`.

Practical implications:

- `aif360.metrics.ot_metric.ot_distance` exists as a helper, but it is not imported from top-level `aif360.metrics`.
- `aif360.sklearn.metrics.ot_distance` is the preferred route for sklearn/pandas workflows and is covered by the sklearn-interface sub-skill.
- Without the extra, imports may warn that OT distance is unavailable or fail when the helper is used.
- Do not treat OT metric output as verified unless the current task environment installs the extra and runs an OT-specific smoke or native test.
