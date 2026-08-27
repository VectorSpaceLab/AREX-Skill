# Data Input Troubleshooting

Use this file when TFLearn data loading or feeds fail before or during `DNN.fit`.

## CSV target and ignore columns

Symptoms:

- Labels look like feature values.
- Feature width is one less or one more than expected.
- The ignored text column still appears in the feature rows.
- `ValueError: could not convert string to float` during `np.asarray(..., dtype=np.float32)`.

Causes and fixes:

1. `target_column` was specified relative to the wrong schema.
   - Count columns in the original CSV row.
   - Use `--target-column` with the original index.
   - Negative values are allowed; `-1` means last column.

2. `columns_to_ignore` shifted unexpectedly after target removal.
   - In `load_csv`, target is popped before ignored features are filtered.
   - Ignore column inputs are original CSV indices; TFLearn shifts ignore indices that were greater than `target_column`.
   - Re-run:
     ```bash
     python scripts/validate_tflearn_tabular_data.py --csv data.csv --target-column 0 --ignore-columns 2,7
     ```

3. Header mismatch.
   - Use `--has-header` for named first rows.
   - Use `--no-header` for raw numeric first rows; otherwise the first sample is discarded.

## `categorical_labels` and `n_classes`

Symptoms:

- Assertion: `n_classes not specified!`
- One-hot target width does not match final output units.
- Index errors while converting labels.

Fixes:

- Pass `n_classes` whenever `categorical_labels=True`.
- Map non-integer labels to deterministic integer ids before one-hot encoding.
- Ensure every label id is `0 <= id < n_classes`.
- Ensure the final classification layer unit count matches `Y.shape[1]`.

Validator command:

```bash
python scripts/validate_tflearn_tabular_data.py \
  --csv data.csv --target-column -1 --categorical-labels --n-classes 3
```

## Feature dtype and object arrays

Symptoms:

- `ValueError: could not convert string to float`.
- `X.dtype == object` after conversion.
- Training fails with TensorFlow feed dtype errors.

Fixes:

- Drop text identifier columns such as names, ticket ids, free text, or URLs.
- Encode categorical columns explicitly, e.g. `female -> 1.0`, `male -> 0.0`, or one-hot encode outside TFLearn.
- Fill or remove blanks before `np.asarray(..., dtype=np.float32)`.
- Use the validator to list per-column conversion failures:
  ```bash
  python scripts/validate_tflearn_tabular_data.py --csv data.csv --target-column 0 --ignore-columns 2,7
  ```

## Shape mismatch between data and `input_data`

Symptoms:

- TensorFlow feed error mentioning placeholder shape.
- TFLearn error containing `Data shape mismatch` or `too few dimensions`/`too many dimensions`.
- Fit starts but target/output dimensions fail when computing loss.

Fixes:

1. Print shapes immediately before fitting:

   ```python
   print('X', np.shape(X), getattr(X, 'dtype', None))
   print('Y', np.shape(Y), getattr(Y, 'dtype', None))
   ```

2. Match input shape to feature axes after the sample axis:

   ```python
   net = tflearn.input_data(shape=[None] + list(np.shape(X)[1:]))
   ```

3. Check sample counts:

   ```python
   assert len(X) == len(Y)
   ```

4. For one-hot classification, check final target width:

   ```python
   assert Y.ndim == 2
   assert Y.shape[1] == n_classes
   ```

5. For multiple inputs, verify every input shares the same axis-0 length and feed by list order or exact input name/placeholder key.

## `np.bool` on modern NumPy

Symptoms:

- `AttributeError: module 'numpy' has no attribute 'bool'`.
- Failure occurs in character sequence helpers or older examples that create boolean one-hot arrays.

Why it happens:

- Older TFLearn code uses `np.bool`, which exists in NumPy 1.18.5 but is removed in modern NumPy.

Preferred fixes:

1. Use the verified legacy-compatible runtime stack: Python 3.7, TensorFlow 1.15.5, NumPy 1.18.5.
2. If you must run a small data utility under modern NumPy, add a local shim before calling the affected function:

   ```python
   import numpy as np
   if not hasattr(np, 'bool'):
       np.bool = np.bool_
   ```

Do not treat the shim as proof that all TensorFlow 1.x training works under a modern TensorFlow/Python stack.

## TensorFlow/protobuf import failures

Symptoms:

- Import fails with missing `tensorflow.python.util.nest.is_sequence`.
- Protobuf descriptor errors mention generated code or descriptor creation.

Fixes:

- Use TensorFlow 1.15.x for TFLearn 0.5.0.
- Pin protobuf to `3.20.3` with TensorFlow 1.15.5.
- Do not expect TensorFlow 2.21/Python 3.13 to import this TFLearn checkout without compatibility patching outside the scope of this sub-skill.

## Missing HDF5 support

Symptoms:

- Console prints `hdf5 is not supported on this machine`.
- `ImportError: No module named h5py`.
- HDF5 feed fails after file was closed.

Fixes:

- Install `h5py` in the same environment as TFLearn.
- Keep the HDF5 file handle open for the full training/prediction call.
- Confirm datasets are indexed by sample axis:
  ```python
  print(X_h5.shape, Y_h5.shape)
  assert len(X_h5) == len(Y_h5)
  ```

## Missing Dask

Symptoms:

- `ImportError: No module named dask`.
- Dask array slicing or chunk errors during `fit`.

Fixes:

- Install `dask[array]` only if Dask-backed feeds are actually needed.
- Use chunk tuples whose length equals the array rank and whose first chunk dimension is the sample chunk size.
- Fall back to NumPy or HDF5 if Dask support is not required.

## Missing Pillow or image loading failures

Symptoms:

- `ImportError` involving `PIL` or `Pillow`.
- Image path cannot be opened.
- Mode/channel mismatch for grayscale/RGBA images.

Fixes:

- Install Pillow.
- For file-mode image lists, use lines formatted as `path class_id` and pass `image_base_path` if paths are relative.
- Use `grayscale=True` only when the model input shape expects one channel.
- Use `filter_channel=True` when you need to skip non-RGB inputs.

## Missing SciPy for image augmentation or SVHN

Symptoms:

- Console prints `Scipy not supported!`.
- Random rotation/blur augmentation fails because `scipy.ndimage` is unavailable.
- SVHN loader fails to read `.mat` files.

Fixes:

- Install SciPy for `ImageAugmentation.add_random_rotation`, `add_random_blur`, or SVHN.
- If SciPy cannot be installed, restrict image augmentation to crops/flips/90-degree rotations and avoid SVHN.

## Dataset download and network failures

Symptoms:

- Loader prints `Downloading ...` and then fails with URL, DNS, timeout, proxy, or permission errors.
- Loader creates a partial archive/file.
- Repeated runs keep trying to download.

Fixes:

- Pass an explicit local data directory and pre-populate it in offline jobs.
- Delete partial files before retrying.
- Verify write permission to the requested cache directory.
- Treat the error as a dataset acquisition issue; model/data shape logic should not be debugged until the files exist.

Examples:

```python
from tflearn.datasets import mnist, cifar10
X, Y, testX, testY = mnist.load_data(data_dir='data/mnist', one_hot=True)
(X, Y), (testX, testY) = cifar10.load_data(dirname='data/cifar-10-batches-py', one_hot=True)
```

## `SequencePreprocessing` or `SequenceAugmentation` not implemented

Symptoms:

- `NotImplementedError` when instantiating `SequenceAugmentation`.
- `NotImplementedError` from `SequencePreprocessing.sequence_padding()`.

Fixes:

- Do not attach those sequence classes for this version.
- Use `tflearn.data_utils.pad_sequences` before fitting.
- Implement any sequence augmentation manually in NumPy/list preprocessing and feed the resulting arrays.

## Multi-input feed keys do not match

Symptoms:

- TFLearn says no input data or cannot match inputs.
- Dictionary feed does not bind to the expected input.

Fixes:

- For list feeds, pass inputs in the order the `input_data` layers were created.
- For dictionary feeds, use exact layer/tensor names such as `'input1:0'` or the placeholder objects themselves.
- Native input tests cover list feeds, dict feeds keyed by layer name, and dict feeds keyed by placeholder.
