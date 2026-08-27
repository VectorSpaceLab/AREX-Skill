# Data Formats

## Purpose

Read this when you need to know how Petastorm stores schemas, metadata, and row-group information on disk.
This is the layout reference for the writer-side route.

## High-level layout

A Petastorm dataset is still a Parquet dataset, but it carries extra metadata so readers can recover schema and row-group behavior.
A typical local layout looks like this:

```text
output_url/
  part-00000-....parquet
  part-00001-....parquet
  _common_metadata
  _metadata   # present when summary metadata is generated
```

## Important metadata keys

| Key | Meaning |
| --- | --- |
| `UNISCHEMA_KEY` | Serialized `Unischema` stored in the dataset metadata |
| `ROW_GROUPS_PER_FILE_KEY` | Number of row groups per file for legacy row-group reconstruction |
| `ROWGROUPS_INDEX_KEY` | Serialized row-group index dictionary |

## Writer-side rules

- `materialize_dataset` is the workflow that attaches Petastorm metadata to a Parquet write.
- `row_group_size_mb` influences the Parquet row-group size.
- `use_summary_metadata=True` asks the writer to rely on summary metadata instead of the older row-group-per-file bookkeeping path.
- `copy_dataset` can preserve only a subset of columns and optionally drop rows with nulls in selected fields.

## Schema mapping

The dataset schema comes from `Unischema`.
That schema determines:

- field order
- field names
- NumPy dtypes
- shape contracts
- nullability
- codec behavior for non-scalar fields

## Plain Parquet vs Petastorm dataset

| Store | Reader choice | Metadata expectation |
| --- | --- | --- |
| Plain Parquet | `make_batch_reader` | No Petastorm schema metadata required |
| Petastorm dataset | `make_reader` | Petastorm schema metadata and row-group information expected |

## Row-group indexes

Row-group indexes are stored in dataset metadata and are loaded on the read side by selector-aware workflows.
The creation path is:

1. build an indexer such as `SingleFieldIndexer`
2. call `build_rowgroup_index`
3. use a matching selector on the read side

## Practical example

- `scripts/smoke_make_minimal_dataset.py` writes a tiny dataset and confirms the expected metadata shape.
- `scripts/smoke_generate_metadata.py` exercises metadata regeneration on an existing dataset.
- `scripts/smoke_copy_dataset.py` proves that the copied dataset still reads back with the new layout.
