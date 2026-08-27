# Metric API reference

## Core building blocks

| Symbol(s) | Purpose | Notes |
| --- | --- | --- |
| `Metric` | Base class for online, attachable metrics. | Subclasses implement `reset`, `update`, and `compute`. |
| `EpochMetric` | Base class for metrics computed after accumulating predictions and targets. | Used by `AveragePrecision`, `ROC_AUC`, `PrecisionRecallCurve`, and other sklearn-backed metrics. |
| `MetricUsage` / `EpochWise` / `BatchWise` / `BatchFiltered` / running variants | Control when a metric resets, updates, and computes. | Usually the default is epoch-wise. |
| `MetricsLambda` | Build a derived metric from other metrics or values. | Supports operator chaining and can compute F-beta-style expressions. |
| `MetricGroup` | Group several metrics under one attachable object. | Returns a mapping of metric results and also populates individual names. |
| `RunningAverage` | Track the running mean of another value or metric. | Useful for loss smoothing and moving averages. |

## Classification and binary metrics

| Symbol(s) | Purpose | Typical inputs | Optional deps |
| --- | --- | --- | --- |
| `Accuracy` | Overall classification accuracy. | `(y_pred, y)` logits or labels. | none |
| `Precision`, `Recall`, `Fbeta` | Class-wise or averaged precision/recall/F-beta. | Binary, multiclass, or multilabel tensors. | none |
| `ConfusionMatrix`, `DiceCoefficient`, `IoU`, `JaccardIndex`, `mIoU` | Confusion-matrix-derived metrics. | Multiclass or multilabel predictions. | none |
| `AveragePrecision`, `PrecisionRecallCurve`, `ROC_AUC`, `RocCurve` | sklearn-backed binary ranking metrics. | Positive-class scores and binary labels. | `scikit-learn` |
| `TopKCategoricalAccuracy`, `ClassificationReport`, `CohenKappa`, `MatthewsCorrCoef` | General classification reporting helpers. | Multiclass labels/logits. | `scikit-learn` for some members |
| `MultiLabelConfusionMatrix`, `Frequency`, `CosineSimilarity`, `Entropy` | Miscellaneous classification helpers. | Depends on metric. | none |

## Regression and clustering

| Symbol(s) | Purpose | Optional deps |
| --- | --- | --- |
| `MeanAbsoluteError`, `MeanSquaredError`, `RootMeanSquaredError` | Error magnitude metrics. | none |
| `MeanAbsoluteRelativeError`, `MedianAbsoluteError`, `MedianAbsolutePercentageError`, `MedianRelativeAbsoluteError` | Robust absolute/relative error metrics. | none |
| `PearsonCorrelation`, `SpearmanRankCorrelation`, `KendallRankCorrelation` | Correlation-based metrics. | `scipy` for some metrics |
| `R2Score` | Coefficient of determination. | none |
| `CalinskiHarabaszScore`, `DaviesBouldinScore`, `SilhouetteScore` | Clustering evaluation metrics. | `scikit-learn` |

## NLP, vision, GAN, fairness, and recommendation

| Symbol(s) | Purpose | Optional deps / notes |
| --- | --- | --- |
| `Bleu`, `Rouge`, `RougeL`, `RougeN`, `CharacterErrorRate`, `Perplexity` | NLP evaluation helpers. | `nltk` and sometimes `filelock` |
| `PSNR`, `SSIM` | Image similarity metrics. | none for SSIM itself |
| `FID`, `InceptionScore` | GAN/image-generation metrics. | `numpy`, `scipy`, and often `torchvision` for default feature extractors |
| `GpuInfo` | GPU memory/utilization reporting. | `pynvml<12` and an NVIDIA GPU |
| `SubgroupAccuracyDifference`, `DemographicParityDifference`, `SelectionRate` | Fairness metrics by subgroup. | no external packages, but group labels are required |
| `HitRate`, `NDCG` | Recommender-system ranking metrics. | none |
| `ObjectDetectionAvgPrecisionRecall`, `MeanAveragePrecision`, `CommonObjectDetectionMetrics`, `coco_tensor_list_to_dict_list` | COCO-style object-detection metrics. | `torchvision` |

## Shape and contract reminders

- Most metrics expect output in the form `(y_pred, y)` or a mapping with compatible keys.
- Some metrics need scores, not discrete predictions. For example, ROC AUC and precision-recall metrics should receive probabilities or confidences.
- `skip_unrolling=True` is useful when the model returns tuples of outputs that should not be automatically flattened.
- Derived metrics such as `Fbeta` require the dependency metrics to use compatible shapes and averaging settings.
- Fairness subgroup metrics expect `group_labels` in the output.
- Recommender metrics expect tensors of shape `(batch, num_items)`.
