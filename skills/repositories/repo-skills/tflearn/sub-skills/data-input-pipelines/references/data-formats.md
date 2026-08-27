# Data Formats for TFLearn Inputs

This reference summarizes the data contracts that TFLearn 0.5.0 expects at the input boundary. It is written so future agents can prepare feeds without reopening the source repository.

## Core feed contract

TFLearn ultimately feeds TensorFlow placeholders created by `tflearn.input_data`.

- The first axis is always the sample/batch axis. Use `None` in `input_data(shape=...)` for variable batch size.
- `DNN.fit(X, Y, ...)` accepts NumPy arrays, Python lists that can become arrays, dictionaries keyed by input layer name or placeholder, and array-like objects that support `len()` and indexed slicing.
- Multiple inputs can be passed as a list in input-layer order or as a dictionary keyed by layer name/placeholder.
- All input arrays and target arrays must have the same number of samples on axis 0.
- Default `input_data` dtype is `tf.float32`; convert most numeric features to `np.float32` before fitting.
- For integer token ids, set `input_data(..., dtype=tf.int32)` only when downstream sequence/embedding layers expect integer ids.

Typical shape mapping:

| Data kind | Example feature object | Matching `input_data(shape=...)` | Target examples |
|---|---|---|---|
| Flat tabular | `X.shape == (n, 6)` | `[None, 6]` | binary one-hot `(n, 2)` or scalar `(n,)` for compatible losses |
| MNIST flattened | `(n, 784)` | `[None, 784]` | `(n, 10)` with one-hot labels |
| MNIST images | `(n, 28, 28, 1)` | `[None, 28, 28, 1]` | `(n, 10)` |
| CIFAR images | `(n, 32, 32, 3)` | `[None, 32, 32, 3]` | `(n, 10)` or `(n, 100)` |
| Token sequences | `(n, maxlen)` integer ids | `[None, maxlen]` or dtype `tf.int32` for embeddings | `(n, n_classes)` |
| Character sequence generator | `(n, maxlen, n_chars)` booleans/floats | `[None, maxlen, n_chars]` | `(n, n_chars)` |
| Multiple inputs | `[X1, X2]`, each `(n, d)` | one `input_data` per input | one shared `Y` whose axis 0 is `n` |

## CSV and tabular data

`tflearn.data_utils.load_csv(filepath, target_column=-1, columns_to_ignore=None, has_header=True, categorical_labels=False, n_classes=None)` returns `(data, target)` as Python lists unless labels are one-hot encoded.

Important behavior:

- `target_column` is the column index in the original CSV row. `-1` means the last column.
- The target value is removed from each row before ignored feature columns are filtered.
- `columns_to_ignore` is a list of original CSV column indices. Internally, indices greater than `target_column` are shifted after the target is removed. To avoid mistakes, reason in terms of the original CSV header and then verify with the validator.
- `has_header=True` consumes and discards the first CSV row.
- With `categorical_labels=True`, `n_classes` must be an `int`; labels are sent to `to_categorical`.
- `load_csv` does not convert feature strings to floats. You must encode or drop text/categorical columns yourself and then create a numeric array.

Titanic-style schema after `load_csv(..., target_column=0, categorical_labels=True, n_classes=2)`:

| Original index | Column | Role | Typical handling |
|---:|---|---|---|
| 0 | `survived` | target | one-hot label width 2 |
| 1 | `pclass` | feature | numeric |
| 2 | `name` | feature | ignore/drop |
| 3 | `sex` | feature | map `female -> 1.0`, `male -> 0.0` |
| 4 | `age` | feature | numeric; handle blanks before `np.float32` conversion |
| 5 | `sibsp` | feature | numeric |
| 6 | `parch` | feature | numeric |
| 7 | `ticket` | feature | ignore/drop |
| 8 | `fare` | feature | numeric |

After dropping name and ticket from the post-target feature rows, the feature width is 6 and the matching input layer is:

```python
net = tflearn.input_data(shape=[None, 6])
```

Validation command for a similar CSV:

```bash
python scripts/validate_tflearn_tabular_data.py \
  --csv titanic_like.csv \
  --target-column 0 \
  --ignore-columns 2,7 \
  --categorical-labels \
  --n-classes 2
```

The script reports original columns, post-target positions, final contiguous feature positions after ignore handling, row count, label classes, and feature conversion issues.

## One-hot and categorical labels

Use `tflearn.data_utils.to_categorical(y, nb_classes=None)` when the target should be a class matrix.

- If `nb_classes` is supplied, labels are cast to `int32`, flattened, and assigned into a zero matrix of shape `(len(y), nb_classes)`.
- If `nb_classes` is omitted, unique labels are discovered from `y` and compared directly; this can work for strings, but explicit integer class mapping is safer for reproducible class order.
- Labels used as indices must be in `[0, nb_classes - 1]`. A label outside the range raises an index error or silently indicates a class-width mistake in downstream logic.
- For `tflearn.regression(..., loss='categorical_crossentropy')`, the final layer unit count and one-hot target width must match.

Recommended pattern:

```python
classes = {label: i for i, label in enumerate(sorted(set(raw_labels)))}
y_ids = np.asarray([classes[v] for v in raw_labels], dtype=np.int32)
Y = tflearn.data_utils.to_categorical(y_ids, nb_classes=len(classes))
```

## Sequence and text formats

### Padded token-id sequences

`tflearn.data_utils.pad_sequences(sequences, maxlen=None, dtype='int32', padding='post', truncating='post', value=0.0)` converts ragged lists to a dense matrix.

- Input: list of lists, e.g. token ids from IMDB.
- Output: shape `(n_sequences, maxlen)`.
- Default padding/truncating are `post`, so zeros are appended and long sequences are cut at the end.
- Use `padding='pre'` or `truncating='pre'` only when the model should preserve sequence suffixes.
- `value=0.0` is the default pad token; keep it consistent with embedding/masking assumptions in the model.

Example:

```python
trainX = pad_sequences(trainX, maxlen=100, value=0.)
net = tflearn.input_data(shape=[None, 100])
```

### Character-level text generation

`tflearn.data_utils.string_to_semi_redundant_sequences(string, seq_maxlen=25, redun_step=3, char_idx=None)` returns `(X, Y, char_idx)`.

- `X.shape == (n_sequences, seq_maxlen, n_chars)`.
- `Y.shape == (n_sequences, n_chars)`.
- `char_idx` maps characters to integer positions; reuse it for generation via `SequenceGenerator(dictionary=char_idx, seq_maxlen=seq_maxlen)`.
- The implementation in older TFLearn uses `np.bool`; modern NumPy removed that alias. See [troubleshooting](troubleshooting.md#npbool-on-modern-numpy).

File helper: `textfile_to_semi_redundant_sequences(path, seq_maxlen=25, redun_step=3, to_lower_case=False, pre_defined_char_idx=None)` reads the file and calls the string helper.

## Bundled dataset loaders

Dataset loaders are convenience functions, not pure local fixtures. Most download files when absent.

| Loader | Call shape | Returns | Downloads when missing | Notes |
|---|---|---|---|---|
| `tflearn.datasets.titanic.download_dataset(filename='titanic_dataset.csv', work_directory='./')` | explicit download | filepath | yes | CSV only; `load_dataset()` is not implemented |
| `tflearn.datasets.mnist.load_data(data_dir='mnist/', one_hot=False)` | images | `trainX, trainY, testX, testY` | yes | images flattened to `(n, 784)` and normalized; labels one-hot if requested |
| `tflearn.datasets.fashion_mnist.load_data(data_dir='fashion_mnist/', one_hot=False)` | images | intended MNIST-like values | yes | Source has a `tests`/`test` typo in returned object; verify before relying on it |
| `tflearn.datasets.cifar10.load_data(dirname='cifar-10-batches-py', one_hot=False)` | images | `(X_train, Y_train), (X_test, Y_test)` | yes | normalized `(n, 32, 32, 3)`; one-hot width 10 if requested |
| `tflearn.datasets.cifar100.load_data(dirname='cifar-100-python', one_hot=False)` | images | `(X_train, Y_train), (X_test, Y_test)` | yes | normalized `(n, 32, 32, 3)`; fine-label one-hot width 100 if requested |
| `tflearn.datasets.imdb.load_data(path='imdb.pkl', n_words=100000, valid_portion=0.1, maxlen=None, sort_by_len=True)` | token sequences | `train, valid, test` tuples | yes for default filename if missing | Returns ragged token id lists; pad before `input_data` |
| `tflearn.datasets.oxflower17.load_data(dirname='17flowers', resize_pics=(224, 224), shuffle=True, one_hot=False)` | images | `X, Y` | yes | Builds/resuses a local pickle after image download/extraction |
| `tflearn.datasets.svhn.load_data(data_dir='svhn/', one_hot=True)` | images | `trainX, trainY, testX, testY` | yes | Requires SciPy `.mat` reader; labels are one-hot width 10 |

Download guidance:

- Pass a project-local `data_dir`/`dirname`/`work_directory` so downloads do not pollute the working directory.
- Pre-create/cache files in offline environments; most loaders only download if expected files are missing.
- Treat loader network errors as data-acquisition failures, not model failures.

## Image arrays, HDF5, and preloaders

Image helper options from `tflearn.data_utils`:

- `image_preloader(target_path, image_shape, mode='file'|'folder', normalize=True, grayscale=False, categorical_labels=True, files_extension=None, filter_channel=False, image_base_path='', float_labels=False)` returns lazy `Preloader` objects `(X, Y)` for paths.
- `build_hdf5_image_dataset(target_path, image_shape, output_path='dataset.h5', mode='file'|'folder', categorical_labels=True, normalize=True, grayscale=False, files_extension=None, chunks=False, image_base_path='', float_labels=False)` builds an HDF5 file with datasets `X` and `Y`.
- Folder mode expects one subdirectory per class. Non-integer folder names are assigned labels in sorted folder order.
- File mode expects whitespace-separated lines: `path class_id`.
- For RGB models, final image shape should be `(n, height, width, 3)`; grayscale helper reshapes preloaded images to include a single channel.

HDF5 fit pattern:

```python
import h5py
h5f = h5py.File('data.h5', 'r')
X = h5f['cifar10_X']
Y = h5f['cifar10_Y']
net = tflearn.input_data(shape=[None, 32, 32, 3])
model.fit(X, Y, batch_size=96)
h5f.close()
```

Keep the HDF5 file open for the entire `fit` call; TFLearn slices HDF5 datasets by sample indices.

## Dask arrays

The Dask example wraps NumPy arrays using `dask.array.from_array` and passes Dask arrays directly to `DNN.fit`.

```python
import dask.array as da
X = da.from_array(np.asarray(X), chunks=(1000, 32, 32, 3))
Y = da.from_array(np.asarray(Y), chunks=(1000, 10))
```

Use chunks aligned with the sample axis and compatible with the array rank. The repository example demonstrates compatibility, but Dask support is optional and depends on installed `dask` plus an array object that supports the slicing TFLearn uses during batching.
