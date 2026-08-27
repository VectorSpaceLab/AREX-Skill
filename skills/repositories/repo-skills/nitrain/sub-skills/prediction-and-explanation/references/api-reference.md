# API reference

## Purpose

Read this for the verified prediction and explainer signatures.

## Prediction API

### `nitrain.Predictor(model, task, sampler=None, expand_dims=-1)`

- Stores the model, task, sampler, and axis used for channel expansion.
- `task` controls the output post-processing path.
- `sampler` should be a Nitrain sampler such as `SliceSampler` when the model
  expects sampled inference input.
- `expand_dims` controls where the extra channel axis is inserted; `None`
  disables the extra expansion.

### `Predictor.predict(dataset)`

- Iterates over the dataset record by record.
- Applies the sampler before model prediction.
- For `SliceSampler`, repositions the sampled axis back into the original slot.
- For segmentation and classification, rounds the output to `uint8`.
- For multidimensional regression outputs, wraps the result in an ANTs image.
- Returns a list of predictions, one per dataset record.

## Explainer API

### `nitrain.OcclusionExplainer(model, sampler=None)`

- Stores the model and optional sampler.
- Exposes a `fit(dataset)` method in the current source tree.

### `OcclusionExplainer.fit(dataset)`

- The inspected implementation is a placeholder and currently returns `1`.
- It does not yet produce a real occlusion map or attribution result.

## Notes that matter

- The predictor assumes the model and sampler agree on geometry.
- The predictor's output type depends on the task and output dimensionality.
- The explainer surface should be treated as a stub until the implementation
  changes.
