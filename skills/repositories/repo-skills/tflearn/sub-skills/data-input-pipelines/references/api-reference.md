# Data Input API Reference

This reference captures the data-facing APIs verified for TFLearn 0.5.0 with TensorFlow 1.15.x.

## Environment facts that affect data APIs

- Verified package stack: TFLearn distribution version `0.5.0`, TensorFlow `1.15.5`, NumPy `1.18.5`.
- CPU backend is required and verified. CUDA is optional and only affects device placement/performance for these data workflows.
- Importing this checkout in modern Python 3.13 with TensorFlow 2.21 fails because `tensorflow.python.util.nest.is_sequence` is missing.
- TensorFlow 1.15.5 requires protobuf `3.20.3`; protobuf 4.x can produce descriptor errors.
- Older text-vectorization code uses `np.bool`, which is removed in modern NumPy. Prefer the verified older NumPy or apply the small compatibility shim described in [troubleshooting](troubleshooting.md#npbool-on-modern-numpy).

## Input layer

```python
tflearn.input_data(
    shape=None,
    placeholder=None,
    dtype=tf.float32,
    data_preprocessing=None,
    data_augmentation=None,
    name='InputData')
```

Use:

- Provide either `shape` or an existing TensorFlow placeholder.
- If `shape` has more than one dimension and does not start with `None`, TFLearn prepends `None` as the batch axis.
- Default dtype is `tf.float32`.
- `data_preprocessing` must be a `DataPreprocessing` subclass object or `None`.
- `data_augmentation` must be a `DataAugmentation` subclass object or `None`.
- The returned tensor has a `.placeholder`-style role in downstream feeds and is stored in TFLearn graph collections.

Examples:

```python
net = tflearn.input_data(shape=[None, 6])
seq = tflearn.input_data(shape=[None, 100], dtype=tf.int32)
image = tflearn.input_data(shape=[None, 32, 32, 3], data_preprocessing=img_prep)
```

## CSV and label utilities

### `load_csv`

```python
tflearn.data_utils.load_csv(
    filepath,
    target_column=-1,
    columns_to_ignore=None,
    has_header=True,
    categorical_labels=False,
    n_classes=None)
```

Returns `(data, target)`.

- `data` is a list of feature rows; values are strings until you convert them.
- `target` is a list unless `categorical_labels=True`, in which case it is a one-hot NumPy array.
- `target_column` is popped from each row before feature columns are ignored.
- If `categorical_labels=True`, `n_classes` must be supplied as an integer.

### `to_categorical`

```python
tflearn.data_utils.to_categorical(y, nb_classes=None)
```

- With `nb_classes`, returns a float matrix `(len(y), nb_classes)` and treats `y` as integer class ids.
- Without `nb_classes`, discovers unique labels and returns comparison columns in NumPy unique order.
- For stable class semantics, pass explicit class ids and `nb_classes`.

### `pad_sequences`

```python
tflearn.data_utils.pad_sequences(
    sequences,
    maxlen=None,
    dtype='int32',
    padding='post',
    truncating='post',
    value=0.0)
```

- Converts ragged list-of-lists into `(n_samples, maxlen)`.
- `padding` and `truncating` are each `'pre'` or `'post'`.
- Raises `ValueError` for unsupported padding/truncating names.

### Character sequence helpers

```python
tflearn.data_utils.string_to_semi_redundant_sequences(
    string,
    seq_maxlen=25,
    redun_step=3,
    char_idx=None)

tflearn.data_utils.textfile_to_semi_redundant_sequences(
    path,
    seq_maxlen=25,
    redun_step=3,
    to_lower_case=False,
    pre_defined_char_idx=None)

tflearn.data_utils.chars_to_dictionary(string)
tflearn.data_utils.random_sequence_from_string(string, seq_maxlen)
tflearn.data_utils.random_sequence_from_textfile(path, seq_maxlen)
```

- `string_to_semi_redundant_sequences` returns `(X, Y, char_idx)`.
- `X` is shaped `(n_sequences, seq_maxlen, n_chars)`.
- `Y` is shaped `(n_sequences, n_chars)`.
- Generated arrays use boolean dtype in the original code.

## Image and array utilities

```python
tflearn.data_utils.shuffle(*arrs)
tflearn.data_utils.image_preloader(...)
tflearn.data_utils.build_hdf5_image_dataset(...)
tflearn.data_utils.load_image(in_image)
tflearn.data_utils.resize_image(in_image, new_width, new_height, out_image=None, resize_mode=Image.ANTIALIAS)
tflearn.data_utils.convert_color(in_image, mode)
tflearn.data_utils.pil_to_nparray(pil_image)
tflearn.data_utils.build_image_dataset_from_dir(...)
```

`shuffle(*arrs)` shuffles arrays in unison along the first axis and asserts equal lengths.

`image_preloader` important parameters:

```python
image_preloader(
    target_path,
    image_shape,
    mode='file',
    normalize=True,
    grayscale=False,
    categorical_labels=True,
    files_extension=None,
    filter_channel=False,
    image_base_path='',
    float_labels=False)
```

`build_hdf5_image_dataset` important parameters:

```python
build_hdf5_image_dataset(
    target_path,
    image_shape,
    output_path='dataset.h5',
    mode='file',
    categorical_labels=True,
    normalize=True,
    grayscale=False,
    files_extension=None,
    chunks=False,
    image_base_path='',
    float_labels=False)
```

## Preprocessing classes

### `DataPreprocessing`

Use for general arrays; applies during training and testing/prediction.

Methods:

- `add_custom_preprocessing(func)`
- `add_samplewise_zero_center()`
- `add_samplewise_stdnorm()`
- `add_featurewise_zero_center(mean=None)`
- `add_featurewise_stdnorm(std=None)`
- `add_zca_whitening(pc=None)`

Notes:

- Featurewise methods without supplied values compute statistics over the training dataset during fit initialization.
- ZCA whitening stores or expects a principal-component matrix compatible with flattened sample shape.

### `ImagePreprocessing`

Subclass for images.

Methods:

- `add_image_normalization()` divides image arrays by 255.
- `add_crop_center(shape)` crops each image center to `(height, width)`.
- `add_samplewise_zero_center(per_channel=False)`
- `add_samplewise_stdnorm(per_channel=False)`
- `add_featurewise_zero_center(mean=None, per_channel=False)`
- `add_featurewise_stdnorm(std=None, per_channel=False)`
- `add_zca_whitening(pc=None)` inherited.

Not implemented in this version:

- `resize(height, width)`
- `blur()`

### `SequencePreprocessing`

The class exists but sequence-specific `sequence_padding()` raises `NotImplementedError`. Use `tflearn.data_utils.pad_sequences` before fitting.

## Augmentation classes

### `DataAugmentation`

Base class; applies only during training flows.

- `apply(batch)` applies registered augmentation methods in order.

### `ImageAugmentation`

Methods:

- `add_random_crop(crop_shape, padding=None)`
- `add_random_flip_leftright()`
- `add_random_flip_updown()`
- `add_random_90degrees_rotation(rotations=[0, 1, 2, 3])`
- `add_random_rotation(max_angle=20.)` — requires SciPy.
- `add_random_blur(sigma_max=5.)` — requires SciPy.

Shape implications:

- Random crop changes image height/width to `crop_shape` unless `padding` and `crop_shape` preserve original dimensions.
- Flips preserve shape.
- Random rotation uses `reshape=False`, so shape is preserved.

### `SequenceAugmentation`

The class constructor raises `NotImplementedError`, and `random_reverse()` is not implemented. Do not attach `SequenceAugmentation` in runtime workflows for this version.

## Data flow internals useful for debugging

`tflearn.data_flow.FeedDictFlow` is the queue-backed batching mechanism behind training feeds.

Key behavior:

- It determines sample count from the first value in the feed dictionary.
- It builds index batches of size `batch_size`.
- It applies `daug_dict` first, then `dprep_dict`, to each batch.
- Validation/test flow receives preprocessing but no augmentation.
- HDF5 datasets are sliced by sample indices when `h5py` is available.

`tflearn.data_flow.generate_data_tensor(X, Y, batch_size, shuffle=True, num_threads=1, capacity=None)` can build TensorFlow queue tensors from arrays or existing tensors, but most high-level workflows should use `DNN.fit` feeds directly.

## Dataset loaders quick reference

```python
from tflearn.datasets import titanic, mnist, imdb, cifar10, oxflower17
```

Common calls:

```python
titanic.download_dataset('titanic_dataset.csv')
X, Y, testX, testY = mnist.load_data(one_hot=True)
(X, Y), (testX, testY) = cifar10.load_data(one_hot=True)
train, valid, test = imdb.load_data(path='imdb.pkl', n_words=10000)
X, Y = oxflower17.load_data(one_hot=True, resize_pics=(224, 224))
```

Loaders may download archives or data files into their default local directories when missing. See [data formats](data-formats.md#bundled-dataset-loaders) for return shapes and download notes.
