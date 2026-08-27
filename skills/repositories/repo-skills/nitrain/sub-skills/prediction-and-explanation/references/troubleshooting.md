# Troubleshooting

## Purpose

Use this for prediction failures and the current explanation-stub behavior.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Wrong prediction shape | The sampler axis or `expand_dims` value does not match the model. | Confirm the model input shape and the sampler axis before calling `Predictor`. |
| Predictions are not ANTs images | The model output is scalar or the task does not produce a multidimensional tensor. | Rebuild the model or choose the correct task. |
| Segmentation output has the wrong labels | The task string or class count does not match the model head. | Re-check `task='segmentation'` versus `task='classification'`. |
| Slice axis appears flipped or misplaced | `SliceSampler` was given the wrong axis. | Match the axis used in training and prediction. |
| `OcclusionExplainer.fit()` returns a trivial value | That is the current behavior of the placeholder implementation. | Do not promise real saliency or attribution; document the stub instead. |
| `Predictor.predict()` fails on the dataset | The dataset is not iterable in the way the predictor expects, or the model cannot accept the sampled batch. | Use a proper `nitrain.Dataset` and verify the sampler output with a tiny smoke batch first. |

## Recovery steps

1. Verify the sample model and the sample dataset separately.
2. Use the same sampler family at inference that the model expects.
3. Test on one example record before running a larger dataset.
4. Treat `OcclusionExplainer` as a stub until the source code grows a real fit
   implementation.

## Good signals

- `Predictor.predict()` returns a list with one prediction per dataset record.
- The prediction shape matches the resampled image shape after the sampled axis
  is restored.
- Regression outputs can be converted back into ANTs images.

## Hand off when

- the issue is actually a model-construction or trainer-default problem;
- the prediction path is correct but the model head is wrong;
- the user really wants an attribution algorithm, not the current placeholder
  API surface.
