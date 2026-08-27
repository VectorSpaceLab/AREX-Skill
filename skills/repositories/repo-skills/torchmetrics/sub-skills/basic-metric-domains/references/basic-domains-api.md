# Basic Metric Domains API

This reference groups the common TorchMetrics tensor-based families by the constructor arguments and input contracts you are most likely to need.

## Classification

### Common class families

- `Accuracy`, `AUROC`, `AveragePrecision`, `F1Score`, `FBetaScore`, `Precision`, `Recall`, `Specificity`, `HammingDistance`, `JaccardIndex`, `MatthewsCorrCoef`, `CohenKappa`, `ConfusionMatrix`, `CalibrationError`, `ExactMatch`, `HingeLoss`, `LogAUC`, `NegativePredictiveValue`, `PrecisionAtFixedRecall`, `RecallAtFixedPrecision`, `SensitivityAtSpecificity`, `SpecificityAtSensitivity`, and `StatScores`.
- Task-specific classes are usually the `Binary*`, `Multiclass*`, or `Multilabel*` variants.
- `Accuracy`, `AUROC`, `AveragePrecision`, `ConfusionMatrix`, `F1Score`, `Precision`, and `Recall` often also exist as task-dispatched convenience wrappers.

### Core constructor patterns

| Argument | Meaning |
| --- | --- |
| `task` | Selects `binary`, `multiclass`, or `multilabel` behavior for task-dispatched wrappers. |
| `num_classes` | Number of classes for multiclass/index inputs. |
| `num_labels` | Number of labels for multilabel inputs. |
| `threshold` | Converts probabilities/logits to labels for binary or multilabel tasks. |
| `average` | `micro`, `macro`, `weighted`, `none`, or `None` depending on metric family. |
| `multidim_average` | Often `global` or `samplewise` for metrics that flatten extra dims. |
| `ignore_index` | Excludes a target value from the metric. |
| `top_k` | Restricts top-k predictions in ranking/precision-style metrics when supported. |
| `validate_args` | Skips validation for speed when you already know the inputs are valid. |

### Input reminders

- Binary metrics typically accept float probabilities/logits or label tensors.
- Multiclass metrics generally accept tensors with class dimension or class indices depending on the family.
- Multilabel metrics usually expect an explicit label axis and can operate on thresholded probabilities.
- Many metrics flatten extra dimensions after the batch dimension.

## Regression

### Common class families

- `MeanSquaredError`, `MeanAbsoluteError`, `MeanAbsolutePercentageError`, `SymmetricMeanAbsolutePercentageError`, `WeightedMeanAbsolutePercentageError`, `R2Score`, `PearsonCorrCoef`, `SpearmanCorrCoef`, `KendallRankCorrCoef`, `KLDivergence`, `JensenShannonDivergence`, `CosineSimilarity`, `ConcordanceCorrCoef`, `ContinuousRankedProbabilityScore`, `CriticalSuccessIndex`, `TweedieDevianceScore`, `ExplainedVariance`, `MinkowskiDistance`, `NormalizedRootMeanSquaredError`, and `RelativeSquaredError`.

### Core constructor patterns

| Argument | Meaning |
| --- | --- |
| `num_outputs` | Number of regression outputs for multi-output metrics. |
| `multioutput` | Reduction across outputs such as `raw_values`, `uniform_average`, or `variance_weighted`. |
| `reduction` | Batch/output reduction such as `mean`, `sum`, `none`, or metric-specific variants. |
| `log_prob` | Treat inputs as log probabilities in divergence-style metrics. |
| `threshold` | Used in some classification-like regression hybrids such as CSI. |

### Input reminders

- Regression metrics usually expect floating tensors of matching shape.
- Multi-output metrics may return scalars, vectors, or per-output tensors.
- `ContinuousRankedProbabilityScore` expects ensemble predictions and a target aligned with the batch dimension.

## Retrieval

### Common class families

- `RetrievalNormalizedDCG`, `RetrievalMAP`, `RetrievalPrecision`, `RetrievalRecall`, `RetrievalMRR`, `RetrievalRPrecision`, `RetrievalFallOut`, `RetrievalHitRate`, `RetrievalAUROC`, and `RetrievalPrecisionRecallCurve`.

### Core constructor patterns

| Argument | Meaning |
| --- | --- |
| `empty_target_action` | How to treat query groups with no positives: `neg`, `pos`, `skip`, or `error`. |
| `ignore_index` | Ignore samples with this target value. |
| `top_k` | Restrict the metric to the top-k predictions per query. |
| `aggregation` | Aggregate over query groups using `mean`, `median`, `min`, `max`, or a custom callable. |
| `adaptive_k` | Some precision/recall variants adapt `k` to each query length. |

### Input reminders

- Retrieval metrics expect `preds`, `target`, and `indexes`.
- `indexes` identify which samples belong to the same query.
- Shapes are flattened before grouping.
- Targets are typically binary, though some metrics allow positive integer targets.

## Clustering and nominal

### Clustering

- `ClusterAccuracy` needs `num_classes` and the `torch_linear_assignment` optional package.
- Other clustering metrics include `AdjustedRandScore`, `AdjustedMutualInfoScore`, `CalinskiHarabaszScore`, `DaviesBouldinScore`, `DunnIndex`, `FowlkesMallowsIndex`, `HomogeneityScore`, `MutualInfoScore`, `NormalizedMutualInfoScore`, `RandScore`, `VMeasureScore`, and `CompletenessScore`.

### Nominal / association

- `CramersV`, `FleissKappa`, `PearsonsContingencyCoefficient`, `TheilsU`, and `TschuprowsT`.
- These metrics operate on categorical or contingency-style inputs.

### Core constructor patterns

| Argument | Meaning |
| --- | --- |
| `bias_correction` | Optional bias correction for some association and clustering measures. |
| `nan_strategy` | How to treat missing values: usually `replace` or `drop`. |
| `nan_replace_value` | Value used when `nan_strategy='replace'`. |
| `mode` | For `FleissKappa`, chooses counts or probabilities. |

## Aggregation helpers

- `MeanMetric`, `SumMetric`, `RunningMean`, and `RunningSum` are useful when you need scalar accumulation rather than a full metric family.
- They still follow the shared Metric lifecycle and can be used in `MetricCollection`.

## Practical choice rule

If the task names a familiar metric but not the task family, decide by the input shape first:

- class labels or probabilities -> classification
- floating predictions and real targets -> regression
- query groups and indexes -> retrieval
- unsupervised labels -> clustering
- categorical association tables -> nominal
