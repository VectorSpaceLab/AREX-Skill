---
name: custom-models-data
description: "Add or adapt PocketFlow datasets, ModelHelper classes, built-in
  model/data combinations, and custom run scripts for compression tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PocketFlow Custom Models and Data

Use this sub-skill when the user wants to add a new dataset, write or adapt a `ModelHelper`, reuse a built-in model/data combination, or create the `*_at_<dataset>_run.py` execution script that hands a helper to PocketFlow learners.

## Route first

- For learner IDs, compression algorithms, distillation, pruning, sparsification, or quantization flags, route to [compression-learners](../compression-learners/SKILL.md).
- For `path.conf`, local/docker/seven launchers, command preview, GPU discovery, or runtime setup, route to [execution-config](../execution-config/SKILL.md).
- Stay here for the Dataset/ModelHelper/run-script contracts and for adapting built-in dataset/model pairs.

## Operating checklist

1. Identify the task shape: image classification uses `(images, one_hot_labels)` iterators; detection-style helpers may return dictionaries and packed object tensors.
2. Choose the closest built-in combination from [built-in-models-datasets.md](references/built-in-models-datasets.md). Prefer adapting a new file rather than editing a built-in helper directly.
3. Implement a dataset subclass that calls `AbstractDataset.__init__(is_train)`, sets the path-dependent file pattern or overrides `build()`, and returns TensorFlow 1.x iterators.
4. Implement `ModelHelper` against the current abstract contract in [api-contracts.md](references/api-contracts.md): call `AbstractModelHelper.__init__(data_format, forward_w_labels=False)`, create no TensorFlow ops in the constructor, and implement dataset, forward, loss, learning-rate, and name properties.
5. Create a run script that imports `ModelHelper`, defines the common PocketFlow flags, calls `create_learner(sm_writer, model_helper)`, and dispatches `train` or `eval`.
6. If the user needs a starter scaffold, use the bundled helper [generate_model_helper_skeleton.py](scripts/generate_model_helper_skeleton.py). This helper is a DisCo template generator, not an official PocketFlow source script.
7. Before running training, validate that `path.conf` uses the dataset key implied by the run script name and that the selected learner supports the helper's forward signature.

## References

- [API contracts](references/api-contracts.md) - exact Dataset, ModelHelper, run-script, data-format, and `forward_w_labels` contracts.
- [Built-in models and datasets](references/built-in-models-datasets.md) - source workflow matrix, data formats, key flags, and path-key conventions.
- [Custom model template](references/custom-model-template.md) - compact implementation recipe distilled from the Fashion-MNIST-style example.
- [Troubleshooting](references/troubleshooting.md) - common data directory, shape, label, TensorFlow 1.x, and run-script failures.

## Safety boundaries

- Do not start downloads or training from this sub-skill. Generate or review code/templates, then route execution setup to [execution-config](../execution-config/SKILL.md).
- Do not assume TensorFlow 2 compatibility; PocketFlow is a TensorFlow 1.x, Python 3.6-era checkout-style codebase.
- Do not claim a bundled helper is part of the upstream PocketFlow repository; bundled helpers live only in this generated skill tree.
