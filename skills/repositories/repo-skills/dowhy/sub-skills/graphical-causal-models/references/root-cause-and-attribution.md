# Root Cause, Attribution, Relevance, and Influence

GCM attribution APIs answer different questions. Choose by the data situation
and the kind of explanation the user needs.

## Decision matrix

| User situation | Use | Required inputs | Output |
|---|---|---|---|
| A target distribution changed between an old baseline dataset and a new dataset, such as service latency before/after a deployment | `gcm.distribution_change` | Reference GCM with assigned mechanisms, `old_data`, `new_data`, `target_node` | Dict of upstream-node contributions to target distribution change, usually in KL-divergence units unless customized. |
| The target mean or variance changed and the user wants a multiply-robust estimator | `gcm.distribution_change_robust` | Reference graph/model, old/new data, target, functional `"mean"` or `"variance"` | Dict of upstream-node contributions to mean or variance change. |
| A specific row or small batch is anomalous and the user asks what caused that anomaly | `gcm.attribute_anomalies` | Fitted `InvertibleStructuralCausalModel`, target node, anomalous rows | Dict mapping upstream nodes to per-row anomaly-score contributions. |
| The user wants anomaly scores for nodes in anomalous rows before attributing them | `gcm.anomaly_scores` | Fitted probabilistic model and anomaly data | Dict mapping each node to anomaly scores for each supplied row. |
| The user asks which direct parent matters most for a target mechanism | `gcm.parent_relevance` | Fitted structural causal model and target node | Parent-edge relevance dict plus noise relevance. |
| The user wants feature relevance for an arbitrary prediction function | `gcm.feature_relevance_distribution` or `gcm.feature_relevance_sample` | Prediction callable, feature samples, subset scoring function | NumPy relevance scores globally or per sample. |
| The user asks how strong a direct edge is | `gcm.arrow_strength` | Fitted probabilistic model and target node | Dict mapping incoming edges to direct influence scores. |
| The user asks which upstream node contributes influence not inherited from parents | `gcm.intrinsic_causal_influence` | Fitted structural model and target node | Dict mapping upstream nodes, including the target, to intrinsic noise contributions. |
| The user asks why one unit's deterministic mechanism output changed between background and foreground values | `gcm.unit_change` | Background/foreground rows, input column names, fitted prediction mechanism(s) | DataFrame of per-unit input and optional mechanism-change contributions. |

## Distribution change versus anomaly attribution

Use `distribution_change` for changed populations, not individual outliers.
Inputs must be two datasets representing old and new regimes. The method fits
old and new cloned mechanisms and systematically replaces mechanisms to explain
how the marginal distribution of a target changed.

Use `attribute_anomalies` for specific anomalous observations. The method
reconstructs the noise values that generated those rows and asks how replacing
each upstream noise value by normal behavior would change the target anomaly
score.

Practical rule:

- "Latency went up after release; which service changed?" →
  `distribution_change` or `distribution_change_robust`.
- "This request had unusually high latency; which component caused this row?" →
  `attribute_anomalies`.

## `gcm.distribution_change`

Expected model state:

- The reference model must have a DAG and assigned mechanisms.
- It does not need to be fitted before the call; the function fits old and new
  cloned models internally.
- If `auto_assignment_quality=None`, assigned mechanisms are cloned and re-fit.
- If `auto_assignment_quality` is set, mechanisms are automatically assigned
  separately on old and new data.

Important parameters:

- `target_node`: attribution is restricted to ancestors of this target plus the
  target itself.
- `invariant_nodes`: nodes whose mechanisms should be treated as unchanged.
- `num_samples`: affects both runtime and accuracy of Shapley estimates.
- `difference_estimation_func`: controls the unit, such as KL divergence,
  mean difference, or variance difference.
- `return_additional_info=True`: also returns mechanism-change indicators and
  the fitted old/new causal models.
- `shapley_config`: use this for large graphs or budgeted approximations.

Interpretation:

- A large positive score indicates that replacing that node's mechanism explains
  a large part of the target distribution change under the selected difference
  measure.
- Near-zero scores do not prove no change; they can also reflect low power,
  model misspecification, insufficient sample size, or cancellation.
- Negative scores are possible when the selected difference measure and Shapley
  decomposition imply that a mechanism change offsets the target change.

## `gcm.distribution_change_robust`

Use the robust method when the target functional is mean or variance and the
user wants a regression/re-weighting/multiply-robust change attribution. It does
not estimate full conditional distributions in the same way as
`distribution_change`; it estimates nuisance regressions and weights for the
selected functional.

Important parameters:

- `target_functional`: currently use `"mean"` or `"variance"`.
- `method`: `"regression"`, `"re-weighting"`, or `"MR"`.
- `xfit` and `xfit_folds`: cross-fitting controls for nuisance estimation.
- `train_size`, `calib_size`, `split_random_state`: sample splitting and
  calibration controls.
- `crop`: lower/upper probability crop for classifier probabilities.
- `shapley_config`: controls contribution approximation.

## `gcm.attribute_anomalies`

Expected model state:

- Use a fitted `InvertibleStructuralCausalModel`.
- Non-root mechanisms must be invertible with respect to noise.
- `anomaly_samples` should contain the same graph-node columns as the fitted
  model and usually only the rows to explain.

Important parameters:

- `target_node`: the anomalous target being explained.
- `anomaly_scorer`: defaults to a median-CDF based scorer if omitted.
- `attribute_mean_deviation`: switches from information-theoretic anomaly
  score attribution to mean-deviation feature relevance.
- `num_distribution_samples`: background target/noise sample count for tail
  probability or relevance estimation.
- `shapley_config`: critical for runtime on many upstream nodes.

Interpretation:

- Scores are per anomalous row.
- Contributions are assigned to upstream nodes and the target itself.
- A downstream node can be visibly anomalous but receive low root-cause score if
  it only inherited an upstream abnormal noise value.

## Direct influence, intrinsic influence, and relevance

Use `arrow_strength` to rank direct incoming edges to a target. By default, the
unit is based on variance for continuous targets and distribution divergence
for categorical targets. Supply `difference_estimation_func` to change the
unit, for example to mean difference.

Use `intrinsic_causal_influence` to measure how much each upstream node's own
noise contributes to a target property. This is useful when descendants inherit
variation from parents and should not be credited for merely passing it along.
Customize `attribution_func` only if the chosen set function is meaningful for
Shapley decomposition; using the mean is usually uninformative because full and
empty noise sets can have the same expectation.

Use `parent_relevance` to explain the fitted mechanism of a target node in
terms of direct parents plus the target mechanism noise. Use
`feature_relevance_distribution` or `feature_relevance_sample` for black-box
prediction callables outside a full GCM.

## Unit-level change attribution

Use `gcm.unit_change` when the user has background and foreground rows and a
fitted deterministic prediction mechanism, and wants per-row contributions of
input changes and optionally mechanism changes. This is not a full GCM graph
query; it is a mechanism-level attribution helper.

Inputs:

- `background_df` and `foreground_df` with matching rows.
- `input_column_names` present in both frames.
- `background_mechanism` implementing DoWhy's prediction-model interface.
- Optional `foreground_mechanism` to include mechanism-change contribution.

The output is a DataFrame whose columns are input names and, when applicable,
`f` for the mechanism contribution.

## Shapley and budget guidance

Many attribution methods are Shapley-based. On graphs with many upstream nodes,
exact enumeration can become expensive. Use:

```python
cfg = gcm.shapley.ShapleyConfig(
    approximation_method=gcm.shapley.ShapleyApproximationMethods.PERMUTATION,
    num_permutations=20,
    n_jobs=1,
)
```

Then pass `shapley_config=cfg` into attribution APIs. Increase permutations,
sample counts, or bootstrap resamples only when the preliminary result is stable
enough to justify the cost.

## Expected reporting pattern

For attribution tasks, report:

1. Chosen API and why it matches the user's data situation.
2. Required model class and whether the model must be fitted first.
3. Input frames and target node required.
4. Runtime controls chosen.
5. Validation caveat: scores rely on graph, mechanism, and sample-size
   assumptions; use evaluation/refutation when conclusions are important.
