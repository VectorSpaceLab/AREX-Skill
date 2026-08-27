---
name: data-pipelines
description: "Use and debug Scenic dataset registry, dataset configs, input
  pipelines, BigTransfer preprocessing, FlexIO, COCO utilities, and data-format
  assumptions without downloading data by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scenic data pipelines

Use this sub-skill when the task is about Scenic dataset registration, `dataset_name`, `dataset_configs`, `train_utils.get_dataset`, TFDS-backed inputs, `tf.data` service behavior, BigTransfer (`bit`) preprocessing, FlexIO, COCO label utilities, or TFRecord/COCO dataset preflights.

## Read/run map

- Read [references/data-pipelines.md](references/data-pipelines.md) for the dataset registry, `@add_dataset`, lazy imports, `train_utils.get_dataset`, TFDS loading, sharding, padding, prefetching, BigTransfer, and FlexIO pipeline construction.
- Read [references/data-formats.md](references/data-formats.md) for common batch keys, `meta_data`, config fields, TFDS/COCO/FlexIO/TFRecord expectations, and when actual external data is required.
- Read [references/troubleshooting.md](references/troubleshooting.md) for unknown datasets, missing TFDS data, optional dependency failures, TensorFlow GPU-memory behavior, BigTransfer/TensorFlow Addons issues, FlexIO/custom preprocessing failures, and `tf.data` service problems.
- Run [scripts/check_dataset_registry.py](scripts/check_dataset_registry.py) when you need a safe registry check. It lists Scenic's lazy dataset names and can optionally import a dataset module or run a registry lookup without constructing a dataset or downloading data.

## Operating rules

1. **Do not download, convert, or mutate data by default.** Registry inspection and module import are safe; calling a dataset builder, `train_utils.get_dataset`, or TFDS `download_and_prepare()` can touch external data.
2. **Resolve unknown dataset names in two phases:** first check the lazy registry names, then decide whether the config uses a project/custom dataset whose registration module must be imported or whether `dataset_name` is a typo.
3. **Preflight before COCO/TFRecord conversion requests.** If no data is present, provide the required layout, annotation, dependency, and output-path checklist; route actual conversion tools to `baselines-and-projects`.
4. **Keep launch mechanics separate.** For full train/eval command construction, config flag plumbing, checkpoint/workdir handling, or distributed launches, use `running-and-training` after the dataset facts are known.
5. **Keep model-consumption semantics separate.** For how models interpret sharded batches, multi-label targets, task heads, or input specs, use `modeling-and-layers` after identifying the batch format here.
