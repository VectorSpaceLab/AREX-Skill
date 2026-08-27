# Basic domain troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `task=` or `num_classes=` errors in classification | The input type does not match the selected task family | Pick the correct task (`binary`, `multiclass`, `multilabel`) and set class counts explicitly for index-based multiclass inputs. |
| A classification metric returns an unexpected shape | `average=None` or `average='none'` is active, or the metric is returning per-class values | Check the return shape before logging or plotting. |
| Class predictions look correct but the score is wrong | Logits, probabilities, and class indices were mixed incorrectly | Use probabilities/logits only where the metric expects them and threshold when needed. |
| `samplewise` classification accuracy fails on some slices | An `ignore_index` mask or sparse batch left an empty per-sample slice | Prefer `multidim_average='global'` for sparse masks, or ensure every sample still has at least one valid label before using `samplewise`. |
| `ignore_index` seems ignored | The target value does not match the metric's expected ignore value or the metric family does not support it | Check the constructor and the family docs. |
| Regression results are `nan` or unstable | Input shapes do not match, or the data contains invalid values | Verify that predictions and targets have the same shape and no unexpected NaNs or infs. |
| Multi-output regression returns a vector when a scalar was expected | A per-output reduction mode is active | Switch to the documented averaging mode if you need a scalar. |
| `Retrieval*` metrics complain about missing `indexes` | The query grouping tensor was omitted or malformed | Pass `indexes` with one id per prediction and target. |
| Retrieval scores are all zero | The metric has no positive targets for some queries, or the wrong `empty_target_action` was chosen | Decide whether empty queries should count as `neg`, `pos`, `skip`, or `error`. |
| `ClusterAccuracy` fails to import or instantiate | `torch_linear_assignment` is missing or the build failed | Install the clustering extra or a CPU build of `torch_linear_assignment`. |
| Nominal association metrics complain about NaNs or categories | The category counts are malformed or the `nan_strategy` is invalid | Use integer category ids or well-formed count tables and choose `replace` or `drop` appropriately. |
| A metric family seems to need plotting or logging help | The issue is really about combining metrics, not the metric math | Route to `../collections-wrappers-plotting/` or `../core-api/` as appropriate. |
