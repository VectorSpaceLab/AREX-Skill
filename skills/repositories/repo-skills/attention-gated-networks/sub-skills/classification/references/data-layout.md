# Classification Data Layout

## Purpose

Read this before preparing ultrasound data or debugging loader failures for the
classification scripts.

## HDF5 structure

The `us` dataset route is backed by `dataio/loader/us_dataset.py`. It expects a
single HDF5 file whose keys are named by split:

```text
label_names            # byte strings, one per class
x_train, p_train       # training images and integer labels
x_val,   p_val         # validation images and integer labels
x_test,  p_test        # test images and integer labels
```

For each split:

- `x_<split>` length must equal `p_<split>` length.
- Each image entry is indexed as `self.images[index][0]` in the source dataset,
  so common layouts are `(N, 1, H, W)` or `(N, 1, H, W, ...)` with the first
  channel selected.
- Labels are converted to `int64` and then returned as Python `int` values.
- `label_names` are decoded from UTF-8 bytes.
- The number of unique classes should match the model config's `output_nc`.

## Config wiring

The bundled classification configs set:

```json
"training": {
  "arch_type": "us",
  "sampler": "weighted2",
  "batchSize": 64,
  "preloadData": false
},
"data_path": {
  "us": ".../preproc_combined_inp_224x288.hdf5"
},
"model": {
  "type": "classifier" or "aggregated_classifier",
  "tensor_dim": "2D",
  "input_nc": 1,
  "output_nc": 14,
  "gpu_ids": [0]
}
```

To make a config portable, replace the original absolute `data_path.us` value
with a path on the current machine. The generated skill intentionally does not
bundle private dataset paths.

## Samplers and label imbalance

`train_classifaction.py` supports three sampler branches:

| `training.sampler` | Behavior |
| --- | --- |
| `stratified` | Uses the local `StratifiedSampler`, assumes 14 classes, samples 2 from each non-background class and more from the most frequent class. Batch size becomes 52. |
| `weighted2` | Uses `WeightedRandomSampler`; multiplies the background weight by `training.bgd_weight_multiplier`. |
| any other value | Uses `WeightedRandomSampler` with per-sample inverse-frequency weights from `UltraSoundDataset`. |

The custom stratified sampler is hard-coded to `n_class = 14`, so prefer the
weighted sampler branch for other class counts unless the source is updated.

## Tiny fixture schema for smoke tests

A tiny HDF5 fixture for loader-only checks can use:

```python
import h5py, numpy as np
with h5py.File('tiny_us.h5', 'w') as f:
    f['label_names'] = np.array([b'class0', b'class1'])
    for split in ['train', 'val', 'test']:
        f[f'x_{split}'] = np.random.randn(4, 1, 32, 32).astype('float32')
        f[f'p_{split}'] = np.array([0, 1, 0, 1], dtype='int64')
```

Do not use this tiny two-class fixture with the stock Sononet configs unless
`model.output_nc` and any sampler assumptions are also changed. The stock
training configs expect 14 classes.

## Common layout checks

Before starting a real training run:

1. Open the HDF5 file and list keys.
2. Confirm `x_train`, `x_val`, `x_test`, `p_train`, `p_val`, and `p_test` exist.
3. Confirm every `x_<split>` and `p_<split>` length matches.
4. Confirm label values are in `[0, output_nc - 1]`.
5. Confirm the transform crop size fits the image dimensions after any padding
   or channel selection.
6. Decide whether `preloadData` is safe for memory; large HDF5 files should use
   `false`.
