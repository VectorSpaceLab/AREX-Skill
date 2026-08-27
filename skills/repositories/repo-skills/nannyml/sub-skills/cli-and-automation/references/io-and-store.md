# IO and Store Reference

## `FileReader`

`FileReader(filepath, read_args=None, credentials=None, fs_args=None)` reads local or cloud-backed CSV/Parquet files through `fsspec`.

Supported suffixes:

- `.csv`
- `.pq`
- `.parquet`

Examples:

```python
from nannyml.io import FileReader

reference = FileReader(filepath='data/reference.csv').read()
analysis = FileReader(filepath='s3://bucket/analysis.parquet', credentials={...}).read()
```

Use `read_args` to pass through pandas options such as `sep`, `chunksize`, or Parquet reader parameters.

## `RawFilesWriter`

`RawFilesWriter(path, credentials=None, fs_args=None)` writes result data frames to a filesystem location.

Use it with `write(result, filename=..., format='parquet'|'csv')`.

```python
from nannyml.io import RawFilesWriter

writer = RawFilesWriter(path='out/results')
writer.write(result, filename='missing-values.parquet', format='parquet')
```

Notes:

- `filename` is required.
- `format` must be `parquet` or `csv`.
- The writer is registered under `raw_files` for config use.

## `PickleFileWriter`

`PickleFileWriter(path, credentials=None, fs_args=None, write_args=None)` pickles the result object itself.

```python
from nannyml.io import PickleFileWriter

writer = PickleFileWriter(path='out/pickles')
writer.write(result, filename='monitoring-result.pkl')
```

Notes:

- `filename` is required.
- The writer is registered under `pickle` for config use.
- Use this when you want to reload the exact result object later.

## `DatabaseWriter`

`DatabaseWriter(connection_string, connection_options=None, model_name=None)` writes result metrics to a SQLAlchemy-compatible database.

```python
from nannyml.io.db import DatabaseWriter

writer = DatabaseWriter(
    connection_string='sqlite:///',
    model_name='demo-model',
)
writer.write(result)
```

Notes:

- `DatabaseWriter` is optional and requires `pip install 'nannyml[db]'`.
- It is registered under `database` for config use.
- It creates the required schema on initialization.
- `model_name` is optional but useful when several models write into the same database.
- The current database writer expects timestamped results.

## `FilesystemStore`

`FilesystemStore(root_path, credentials=None, fs_args=None, serializer=...)` caches fitted calculators or estimators between runs.

```python
from nannyml.io.store import FilesystemStore

store = FilesystemStore(root_path='out/cache')
store.store(calc, filename='cbpe.pkl')
loaded = store.load(filename='cbpe.pkl', as_type=type(calc))
```

Behavior:

- `store(...)` persists the fitted object.
- `load(...)` returns the object or `None` if no file exists.
- `as_type` checks the loaded object type when provided.
- `filename` is required for both `store` and `load` in this implementation.
- Works with local paths and fsspec-backed cloud paths.

## Writer factory keys

The config layer uses `WriterFactory` keys:

- `raw_files`
- `pickle`
- `database`

These keys correspond to the writer classes above.

## Common automation pattern

1. Read the reference and analysis files with `FileReader`.
2. Fit the calculator on reference.
3. Store the fitted calculator in a `FilesystemStore` if repeated runs are expected.
4. Write the result with `RawFilesWriter`, `PickleFileWriter`, or `DatabaseWriter`.
5. In CLI runs, move those choices into the calculator's `outputs` and `store` config blocks.
