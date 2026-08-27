---
name: data-input-pipelines
description: "Prepare, validate, and attach TFLearn data feeds, preprocessing,
  and augmentation objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Input Pipelines

Use this sub-skill when the task is about making data acceptable to TFLearn before training or prediction: CSV/tabular loading, categorical labels, sequence/text vectorization, bundled dataset loaders, NumPy/list/HDF5/Dask feeds, and `DataPreprocessing`/`DataAugmentation` objects attached through `tflearn.input_data`.

## Start here

1. Classify the input source and expected tensor shape using [data formats](references/data-formats.md).
2. For tabular CSV, run the bundled validator before building a model:
   ```bash
   python scripts/validate_tflearn_tabular_data.py --csv data.csv --target-column 0 --categorical-labels --n-classes 2
   ```
3. Follow the appropriate recipe in [workflows](references/workflows.md) for CSV, sequences/text, dataset loaders, HDF5, Dask, image preprocessing, or multi-input feeds.
4. Check exact function signatures and gotchas in [API reference](references/api-reference.md).
5. If import, dtype, optional dependency, download, or shape errors occur, use [troubleshooting](references/troubleshooting.md).

## Operating rules

- Always separate **data preparation** from architecture work. This sub-skill may decide `input_data(shape=...)`, placeholder dtype, and label width; route hidden layers, losses beyond label compatibility, and model architecture choices to `layers-and-ops`.
- Always verify the first dimension of every feed is the sample axis and that all inputs/targets have the same number of samples.
- Convert feature arrays to numeric NumPy arrays, normally `np.float32`, before fitting unless a specific placeholder uses another dtype.
- For classification with `categorical_crossentropy`, provide one-hot labels using loader `one_hot=True`, `load_csv(..., categorical_labels=True, n_classes=...)`, or `tflearn.data_utils.to_categorical`.
- Attach preprocessing and augmentation at `input_data`; preprocessing applies during training and evaluation/prediction, while augmentation applies during training only.
- Keep training loops, checkpoints, save/load, callbacks, and `DNN.fit` persistence behavior outside this sub-skill except for the feed-shape requirements needed by `fit`.

## Quick routing map

| User need | Use |
|---|---|
| CSV target column, ignored columns, one-hot labels, object dtype | [data formats](references/data-formats.md#csv-and-tabular-data) and bundled validator |
| Titanic-style workflow | [workflows](references/workflows.md#tabular-csv-titanic-style) |
| IMDB/list-of-token sequences or character text generation inputs | [workflows](references/workflows.md#sequence-and-text-inputs) |
| MNIST/CIFAR/IMDB/Titanic/flower/SVHN loaders and downloads | [data formats](references/data-formats.md#bundled-dataset-loaders) |
| HDF5 or Dask arrays passed to `DNN.fit` | [workflows](references/workflows.md#hdf5-and-dask-feeds) |
| Image preprocessing/augmentation | [workflows](references/workflows.md#realtime-preprocessing-and-augmentation) |
| Missing optional packages, `np.bool`, TensorFlow 2 import failures | [troubleshooting](references/troubleshooting.md) |
