# Connectors, loaders, metadata, and relationships

## Data connectors

```python
from sdgx.data_connectors.csv_connector import CsvConnector
from sdgx.data_connectors.dataframe_connector import DataFrameConnector
from sdgx.data_connectors.generator_connector import GeneratorConnector
```

- `CsvConnector(path, sep=",", header="infer", **read_csv_kwargs)` wraps `pandas.read_csv`. It supports `read(offset, limit)`, `iter(offset, chunksize)`, `columns()`, and a SHA-256 based identity.
- `DataFrameConnector(df)` wraps a small `pandas.DataFrame` and returns slices without disk cache.
- `GeneratorConnector(generator_caller)` accepts a callable returning a generator of DataFrames. Passing `offset=0` resets the generator, but arbitrary offsets are not true random access.

## DataLoader

```python
from sdgx.data_loader import DataLoader
loader = DataLoader(connector, chunksize=10000, cacher_kwargs={"cache_dir": "cache/sdgx"})
```

`DataLoader` combines a connector and cacher. It supports `columns()`, `keys()`, `load_all()`, `iter()`, slicing, `shape`, and `finalize(clear_cache=True)`.

Defaults:

- `DataFrameConnector` uses `NoCache`.
- Other connectors use `DiskCache`, which writes parquet blocks and requires pyarrow.
- `GeneratorConnector` cannot use `NoCache`; use `DiskCache` or another real cacher.

## Metadata

```python
from sdgx.data_models.metadata import Metadata
metadata = Metadata.from_dataframe(df, check=False)
```

Important fields and methods:

- `column_list`, `primary_keys`, `id_columns`, `int_columns`, `float_columns`, `bool_columns`, `discrete_columns`, `datetime_columns`, `const_columns`, and `pii_columns`.
- `datetime_format`, `numeric_format`, `categorical_encoder`, and `categorical_threshold`.
- `get`, `set`, `add`, `delete`, `update`, `query`, `get_column_data_type`, `get_column_pii`, `change_column_type`, `remove_column`, `save`, and `load`.

## Multi-table primitives

```python
from sdgx.data_models.relationship import Relationship
from sdgx.data_models.combiner import MetadataCombiner
```

`Relationship.build` validates non-empty tables, non-empty foreign keys, different parent/child names, and optional metadata compatibility. `MetadataCombiner` groups named metadata and relationships and can `save`/`load` directories.
