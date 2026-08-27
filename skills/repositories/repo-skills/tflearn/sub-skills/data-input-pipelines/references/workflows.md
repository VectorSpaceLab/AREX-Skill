# Data Input Workflows

Use these workflows to turn common data sources into feeds that TFLearn can consume. Architecture details are intentionally limited to `input_data` shape and dtype decisions.

## Tabular CSV, Titanic style

Goal: load a CSV whose target is one column, ignore non-useful text columns, encode remaining categories, and feed numeric features.

1. Validate the raw CSV shape and labels.

   ```bash
   python scripts/validate_tflearn_tabular_data.py \
     --csv titanic_like.csv \
     --target-column 0 \
     --ignore-columns 2,7 \
     --categorical-labels \
     --n-classes 2
   ```

   Expected signal:
   - nonzero `rows`;
   - target column reported correctly;
   - ignored columns are not in the inferred feature list;
   - `label classes` show values inside the requested class width;
   - remaining conversion issues are only for columns you plan to encode manually.

2. Load with TFLearn.

   ```python
   from tflearn.data_utils import load_csv

   data, labels = load_csv(
       'titanic_like.csv',
       target_column=0,
       categorical_labels=True,
       n_classes=2)
   ```

3. Drop or encode non-numeric feature columns, then convert to float.

   ```python
   import numpy as np

   def preprocess(rows, columns_to_delete):
       # columns_to_delete are positions in the post-target feature row.
       for column in sorted(columns_to_delete, reverse=True):
           [row.pop(column) for row in rows]
       for row in rows:
           # Example: after target removal and name deletion, sex is feature id 1.
           row[1] = 1.0 if row[1] == 'female' else 0.0
       return np.asarray(rows, dtype=np.float32)

   X = preprocess(data, columns_to_delete=[1, 6])
   Y = labels
   ```

4. Match `input_data` to the post-preprocessing feature width.

   ```python
   net = tflearn.input_data(shape=[None, X.shape[1]])
   ```

5. Before training, assert shape compatibility.

   ```python
   assert len(X) == len(Y)
   assert X.dtype == np.float32
   assert Y.shape[1] == 2
   ```

Notes:

- `load_csv(columns_to_ignore=...)` can ignore original columns too, but manual deletion after loading is often clearer when you still need to inspect or encode categorical strings.
- If the target is not the first column, remember that feature-row positions after `load_csv` differ from original CSV positions because the target has been popped.

## Generic NumPy/list feeds

1. Convert features and labels to arrays after any manual preprocessing.

   ```python
   X = np.asarray(X, dtype=np.float32)
   Y = np.asarray(Y, dtype=np.float32)
   ```

2. Use the sample axis as axis 0.

   ```python
   assert X.shape[0] == Y.shape[0]
   net = tflearn.input_data(shape=[None] + list(X.shape[1:]))
   ```

3. For scalar labels, decide whether to one-hot encode.

   ```python
   from tflearn.data_utils import to_categorical
   Y = to_categorical(y_ids, nb_classes=n_classes)
   ```

4. For multiple inputs, create one named `input_data` per input and feed a list or dictionary.

   ```python
   input1 = tflearn.input_data(shape=[None, 1], name='input1')
   input2 = tflearn.input_data(shape=[None, 1], name='input2')

   # Later, either list order:
   model.fit([X1, X2], Y, batch_size=32)

   # Or dict by input layer/tensor name:
   model.fit({'input1:0': X1, 'input2:0': X2}, Y, batch_size=32)
   ```

   Native input tests verify list feeds, dictionaries keyed by layer name, and dictionaries keyed by placeholders.

## Sequence and text inputs

### IMDB-style token sequences

```python
from tflearn.datasets import imdb
from tflearn.data_utils import pad_sequences, to_categorical

train, valid, test = imdb.load_data(path='imdb.pkl', n_words=10000, valid_portion=0.1)
trainX, trainY = train
testX, testY = test

trainX = pad_sequences(trainX, maxlen=100, value=0.)
testX = pad_sequences(testX, maxlen=100, value=0.)
trainY = to_categorical(trainY, nb_classes=2)
testY = to_categorical(testY, nb_classes=2)

net = tflearn.input_data(shape=[None, 100])
```

Checks:

```python
assert trainX.shape[1] == 100
assert trainY.shape[1] == 2
assert trainX.shape[0] == trainY.shape[0]
```

Use `dtype=tf.int32` at `input_data` only when the downstream layer consumes integer token ids directly.

### Character-level text generator inputs

```python
from tflearn.data_utils import textfile_to_semi_redundant_sequences

maxlen = 25
X, Y, char_idx = textfile_to_semi_redundant_sequences(
    'corpus.txt', seq_maxlen=maxlen, redun_step=3, to_lower_case=True)

net = tflearn.input_data(shape=[None, maxlen, len(char_idx)])
```

Checks:

```python
assert X.shape[1] == maxlen
assert X.shape[2] == len(char_idx)
assert Y.shape[1] == len(char_idx)
```

If this fails on modern NumPy with `module 'numpy' has no attribute 'bool'`, use the compatibility guidance in [troubleshooting](troubleshooting.md#npbool-on-modern-numpy) or run in the verified older stack.

## Bundled dataset loaders

Use loaders for quick experiments, but treat them as networked data acquisition.

```python
from tflearn.datasets import mnist, cifar10

X, Y, testX, testY = mnist.load_data(one_hot=True)
# X/testX are flattened and normalized: shape (n, 784)
net = tflearn.input_data(shape=[None, 784])

(X, Y), (testX, testY) = cifar10.load_data(one_hot=True)
# X/testX are normalized RGB images: shape (n, 32, 32, 3)
net = tflearn.input_data(shape=[None, 32, 32, 3])
```

For reproducible/offline runs:

- choose a local cache directory (`data_dir`, `dirname`, or `work_directory`);
- pre-populate the expected files;
- keep the loader call but do not assume network access;
- verify returned shapes before building the network.

## HDF5 and Dask feeds

### HDF5

Use HDF5 when arrays are too large for RAM or when you want lazy disk-backed slicing.

```python
import h5py
import numpy as np

# One-time write.
with h5py.File('data.h5', 'w') as h5f:
    h5f.create_dataset('X', data=np.asarray(X, dtype=np.float32))
    h5f.create_dataset('Y', data=np.asarray(Y, dtype=np.float32))

# Training-time read. Keep file open until fit completes.
h5f = h5py.File('data.h5', 'r')
X_h5 = h5f['X']
Y_h5 = h5f['Y']
net = tflearn.input_data(shape=[None] + list(X_h5.shape[1:]))
# model.fit(X_h5, Y_h5, batch_size=...)
h5f.close()
```

Operational checks:

- `h5py` must import successfully.
- Datasets must expose `len(dataset)` and sample-index slicing.
- Keep labels in a separate dataset with axis 0 aligned to `X`.
- Close the file after training, not before.

### Dask

Use Dask only when `dask.array` is installed and the array chunks are compatible with sample-axis batching.

```python
import dask.array as da

X_da = da.from_array(np.asarray(X), chunks=(1000,) + X.shape[1:])
Y_da = da.from_array(np.asarray(Y), chunks=(1000,) + Y.shape[1:])
net = tflearn.input_data(shape=[None] + list(X.shape[1:]))
# model.fit(X_da, Y_da, batch_size=96)
```

Avoid one-size chunks such as `(1000, 1000, 1000, 1000)` for arrays whose rank or dimensions do not match. Match chunk tuple length to array rank.

## Realtime preprocessing and augmentation

Attach preprocessing and augmentation objects to the input layer:

```python
from tflearn.data_preprocessing import ImagePreprocessing
from tflearn.data_augmentation import ImageAugmentation

img_prep = ImagePreprocessing()
img_prep.add_featurewise_zero_center()
img_prep.add_featurewise_stdnorm()

img_aug = ImageAugmentation()
img_aug.add_random_flip_leftright()
img_aug.add_random_rotation(max_angle=25.)

net = tflearn.input_data(
    shape=[None, 32, 32, 3],
    data_preprocessing=img_prep,
    data_augmentation=img_aug)
```

Behavior:

- `DataPreprocessing` methods are applied during training and testing/prediction flows.
- `DataAugmentation` methods are applied during training flows only.
- Featurewise preprocessing with no supplied mean/std computes persistent values over the training dataset at fit initialization; this can take time. Supply `mean=` or `std=` if you have stable precomputed values.
- `ImagePreprocessing.add_featurewise_zero_center(per_channel=True)` and `add_featurewise_stdnorm(per_channel=True)` compute per-channel statistics.
- Random rotations and blur require SciPy.
- `SequencePreprocessing` and `SequenceAugmentation` exist but their sequence-specific methods are `NotImplementedError`; use `pad_sequences` and manual sequence augmentation instead.

## Optional image dataset builders

For image folders or `path class_id` text files:

```python
from tflearn.data_utils import image_preloader, build_hdf5_image_dataset

X, Y = image_preloader(
    'images.txt', image_shape=(128, 128), mode='file',
    categorical_labels=True, normalize=True)

build_hdf5_image_dataset(
    'images.txt', image_shape=(128, 128), mode='file',
    output_path='images.h5', categorical_labels=True, normalize=True)
```

Choose `image_preloader` for small experiments and `build_hdf5_image_dataset` for larger repeated runs. Both require Pillow; HDF5 creation additionally requires `h5py`.

## Pre-fit validation checklist

Run these checks before handing data to training code:

```python
assert len(X) == len(Y), 'feature/label sample count mismatch'
assert list(np.shape(X))[1:] == net_input_shape_without_batch
assert not np.asarray(X[: min(len(X), 3)]).dtype.kind == 'O', 'object dtype remains'
```

For one-hot classification:

```python
assert Y.ndim == 2
assert Y.shape[1] == n_classes
```

For multi-input:

```python
n = len(Y)
for x in [X1, X2]:
    assert len(x) == n
```
