# API Reference

## Purpose

Read this when you need verified signatures or behavior for dataset creation, copy, metadata repair, or row-group indexing.
The signatures below were checked against the installed package snapshot.

## Schema and row helpers

| Symbol | Signature | Notes |
| --- | --- | --- |
| `Unischema` | `Unischema(name, fields)` | Defines field order, shapes, codecs, and nullability. |
| `UnischemaField` | `UnischemaField(name, numpy_dtype, shape, codec=None, nullable=False)` | Immutable field descriptor. |
| `dict_to_spark_row` | `dict_to_spark_row(unischema, row_dict)` | Validates and converts a Python dictionary into a Spark row. |
| `match_unischema_fields` | `match_unischema_fields(unischema, patterns)` | Resolves regex-style field selectors. |
| `edit_field` | `edit_field(name, numpy_dtype, shape, nullable=False)` | Convenience helper for `TransformSpec.edit_fields`. |
| `TransformSpec` | `TransformSpec(func=None, edit_fields=None, removed_fields=None, selected_fields=None)` | Schema-transform contract used while reading and writing. |

## Codec classes

| Codec | Notes |
| --- | --- |
| `ScalarCodec(spark_type)` | Stores scalar data in a Spark scalar column. |
| `NdarrayCodec()` | Stores NumPy arrays as binary `.npy` payloads. |
| `CompressedNdarrayCodec()` | Stores compressed NumPy arrays as `.npz` payloads. |
| `CompressedImageCodec(image_codec='png', quality=80)` | Compresses image arrays with OpenCV. |

## Dataset writing and repair

| Symbol | Signature | Notes |
| --- | --- | --- |
| `materialize_dataset` | `materialize_dataset(spark, dataset_url, schema, row_group_size_mb=None, use_summary_metadata=False, filesystem_factory=None)` | Context manager that stamps Petastorm metadata on a Parquet write. |
| `get_schema` | `get_schema(dataset)` | Retrieves the stored `Unischema` from a Parquet dataset. |
| `get_schema_from_dataset_url` | `get_schema_from_dataset_url(dataset_url_or_urls, hdfs_driver='libhdfs3', storage_options=None, filesystem=None)` | Convenience wrapper around the dataset lookup path. |
| `generate_petastorm_metadata` | `generate_petastorm_metadata(spark, dataset_url, unischema_class=None, use_summary_metadata=False, hdfs_driver='libhdfs3')` | Rebuilds metadata for an existing dataset. |
| `load_row_groups` | `load_row_groups(dataset)` | Splits a dataset into row-group pieces using metadata when available. |

## Copy and indexing helpers

| Symbol | Signature | Notes |
| --- | --- | --- |
| `copy_dataset` | `copy_dataset(spark, source_url, target_url, field_regex, not_null_fields, overwrite_output, partitions_count, row_group_size_mb, hdfs_driver='libhdfs3')` | Copies, filters, and optionally repartitions a dataset. |
| `args_parser` | `args_parser()` | CLI parser for `petastorm-copy-dataset.py`. |
| `build_rowgroup_index` | `build_rowgroup_index(dataset_url, spark_context, indexers, hdfs_driver='libhdfs3')` | Builds and stores row-group index metadata. |
| `get_row_group_indexes` | `get_row_group_indexes(dataset)` | Loads row-group indexes from dataset metadata. |
| `SingleFieldIndexer` | `SingleFieldIndexer(index_name, index_field)` | Indexes a single scalar or array-like field. |
| `FieldNotNullIndexer` | `FieldNotNullIndexer(index_name, index_field)` | Records row groups where a field has at least one non-null value. |
| `RowGroupSelectorBase` | abstract base class | Consumed on the read side by `rowgroup_selector`. |

## Filesystem helpers

| Symbol | Signature | Notes |
| --- | --- | --- |
| `FilesystemResolver` | `FilesystemResolver(dataset_url, hadoop_configuration=None, connector=HdfsConnector, hdfs_driver='libhdfs3', user=None, storage_options=None)` | Resolves local, HDFS, S3, and GCS URLs. |
| `get_filesystem_and_path_or_paths` | `get_filesystem_and_path_or_paths(url_or_urls, hdfs_driver='libhdfs3', storage_options=None, filesystem=None)` | Returns a filesystem object and one path or a path list. |
| `normalize_dir_url` | `normalize_dir_url(dataset_url)` | Trims trailing slashes from directory URLs. |

## Verified behavior worth remembering

- `materialize_dataset` is the writer-side Petastorm contract: it wraps the Spark write and then adds metadata.
- `generate_petastorm_metadata` can infer the schema from the dataset if the schema metadata is still readable.
- `copy_dataset` raises if the requested field regexes match nothing.
- `build_rowgroup_index` expects compatible indexers and uses Spark to distribute the work.
- `FieldNotNullIndexer` is useful when a selector should include row groups containing at least one non-null value.

## Common writer-side shape rules

- Scalar fields use `shape=()`.
- Variable-length dimensions use `None` in the shape tuple.
- Non-scalar fields need a codec.
- `nullable=False` fields must be present in every written row.
- `nullable=True` fields can be omitted only if the writer or transform later fills them in.
