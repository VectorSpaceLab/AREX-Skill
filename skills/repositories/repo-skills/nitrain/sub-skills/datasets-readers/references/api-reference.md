# API reference

## Purpose

Read this when you need the exact dataset and reader constructors or when a
future agent needs to reason about how records are assembled.

## Verified public API

### `nitrain.Dataset(inputs, outputs, transforms=None, base_dir=None, base_file=None)`

- Normalizes `inputs` and `outputs` through `infer_reader()`.
- Resolves `base_dir` with `os.path.expanduser()` when present.
- Applies `map_values()` on both readers and warns if mapped lengths differ.
- `select(n, random=False)` returns a deep-copied subset.
- `split(p, random=False)` accepts `float`, 2-tuple, or 3-tuple partitions.
- `__getitem__` returns `(x, y)` pairs and supports slices.

### `nitrain.GoogleCloudDataset(bucket, inputs, outputs, transforms=None, base_dir=None, base_file=None, credentials=None)`

- Maps readers through `map_gcs_values()` instead of local file paths.
- Uses a service-account JSON file path or credential object.
- Returns the same `Dataset`-style interface once mapped.

### `nitrain.fetch_data(name, path=None, overwrite=False)`

- `example-01` creates a tiny local directory with synthetic NIfTI files and a
  `participants.csv` table.
- `openneuro/...` uses `datalad` and network access.
- The default cache root is the package-managed `~/.nitrain` directory unless
  `path` is given, and the `NITRAIN_DIR` environment variable can override that
  cache root.

### Reader constructors

- `ImageReader(pattern, base_dir=None, exclude=None, label=None)`
- `ColumnReader(column, base_file=None, is_image=False, label=None)`
- `FolderNameReader(pattern, base_dir=None, exclude=None, label=None, level=0, format='string')`
- `MemoryReader(data, label=None)`
- `ComposeReader(readers, label=None)`

### Reader helpers

- `infer_reader(x)` turns lists, dicts, arrays, scalars, and existing readers
  into a concrete reader object.
- `is_reader(x)` is a type-string check used internally.
- `flatten_readers()` is present but not part of the usual user-facing flow.

## Notes that matter in practice

- `ColumnReader.is_image=True` means the column stores file paths that should be
  loaded as ANTs images.
- `FolderNameReader(format='integer')` returns class indices and
  `format='onehot'` returns one-hot lists.
- Nested dict/list structures become aligned `ComposeReader` trees.
- `Dataset.__repr__()` shows the current input, output, and transform summary.
