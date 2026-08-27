# API Reference

## Purpose

Read this when you need verified call signatures or the rough contract of the reader and adapter APIs without reopening the source tree.
The signatures below were checked against the installed package snapshot.

## Core reader entry points

| Symbol | Signature | Notes |
| --- | --- | --- |
| `make_reader` | `make_reader(dataset_url, schema_fields=None, reader_pool_type='thread', workers_count=10, pyarrow_serialize=False, results_queue_size=50, seed=None, shuffle_rows=False, shuffle_row_groups=True, shuffle_row_drop_partitions=1, predicate=None, rowgroup_selector=None, num_epochs=1, cur_shard=None, shard_count=None, shard_seed=None, cache_type='null', cache_location=None, cache_size_limit=None, cache_row_size_estimate=None, cache_extra_settings=None, hdfs_driver='libhdfs3', transform_spec=None, filters=None, storage_options=None, zmq_copy_buffers=True, filesystem=None, convert_early_to_numpy=False)` | Petastorm datasets only. Supports row-level predicates, row-group selectors, shuffling, caching, sharding, and transforms. |
| `make_batch_reader` | `make_batch_reader(dataset_url_or_urls, schema_fields=None, reader_pool_type='thread', workers_count=10, results_queue_size=50, seed=None, shuffle_rows=False, shuffle_row_groups=True, shuffle_row_drop_partitions=1, predicate=None, rowgroup_selector=None, num_epochs=1, cur_shard=None, shard_count=None, shard_seed=None, cache_type='null', cache_location=None, cache_size_limit=None, cache_row_size_estimate=None, cache_extra_settings=None, hdfs_driver='libhdfs3', transform_spec=None, filters=None, storage_options=None, zmq_copy_buffers=True, filesystem=None, convert_early_to_numpy=False)` | Batch-oriented reader for plain Parquet stores and also usable on Petastorm datasets. |
| `Reader` | `Reader(pyarrow_filesystem, dataset_path, schema_fields=None, seed=None, shuffle_rows=False, shuffle_row_groups=True, shuffle_row_drop_partitions=1, predicate=None, rowgroup_selector=None, reader_pool=None, num_epochs=1, cur_shard=None, shard_count=None, cache=None, worker_class=None, transform_spec=None, is_batched_reader=False, filters=None, shard_seed=None, convert_early_to_numpy=False)` | Lower-level reader object returned by the factory functions. |

## Framework adapters

| Symbol | Signature | Notes |
| --- | --- | --- |
| `tf_tensors` | `tf_tensors(reader, shuffling_queue_capacity=0, min_after_dequeue=0)` | Returns a TensorFlow namedtuple of tensors. Raises on `shuffling_queue_capacity > 0` when the reader already emits batched output. |
| `make_petastorm_dataset` | `make_petastorm_dataset(reader)` | Builds a `tf.data.Dataset` from a reader. Repetition should usually be controlled with reader epochs or cache-before-repeat patterns. |
| `DataLoader` | `DataLoader(reader, batch_size=1, collate_fn=decimal_friendly_collate, shuffling_queue_capacity=0)` | PyTorch adapter for row-wise readers. |
| `BatchedDataLoader` | `BatchedDataLoader(reader, batch_size=1, transform_fn=None, shuffling_queue_capacity=0)` | Torch-oriented batching helper for faster tensor-only paths. |
| `InMemBatchedDataLoader` | `InMemBatchedDataLoader(reader, batch_size=1, transform_fn=None, num_epochs=1, seed=0, rows_capacity=1024, shuffle=False)` | Single-use in-memory batching helper. |

## Sampling, selectors, and structure helpers

| Symbol | Signature | Notes |
| --- | --- | --- |
| `WeightedSamplingReader` | `WeightedSamplingReader(readers, probabilities)` | Samples from multiple readers with normalized probabilities. Readers must share schema, `batched_output`, and ngram state. |
| `NGram` | `NGram(fields, delta_threshold, timestamp_field, timestamp_overlap=True)` | Requires sorted timestamps and returns ngram dictionaries keyed by relative timestep. |
| `SingleIndexSelector` | `SingleIndexSelector(index_name, values_list)` | Selects row groups that contain any requested index values. |
| `IntersectIndexSelector` | `IntersectIndexSelector(single_index_selectors)` | Intersects multiple selectors. |
| `UnionIndexSelector` | `UnionIndexSelector(single_index_selectors)` | Unions multiple selectors. |
| `dataset_as_rdd` | `dataset_as_rdd(dataset_url, spark_session, schema_fields=None, hdfs_driver='libhdfs3')` | Converts a Petastorm dataset to a Spark RDD of namedtuples. |

## Reader argument reminders

- `schema_fields` may be a list of fields or regex-like selectors. For `make_reader`, an `NGram` object is also valid.
- `reader_pool_type` accepts `thread`, `process`, or `dummy`.
- `cache_type` accepts `null` or `local-disk`.
- `predicate` is applied per row in `make_reader` and per batch in `make_batch_reader`.
- `rowgroup_selector` must return row-group indexes and is most useful with generated row-group metadata.
- `filters` are passed to PyArrow parquet scanning.
- `convert_early_to_numpy=True` is a reader optimization for early conversion to NumPy dicts.

## Read-side special cases

- `make_reader` warns if the store is not a Petastorm dataset and suggests `make_batch_reader` for plain Parquet.
- `make_batch_reader` still reads row-group batches from Petastorm datasets, but the API is shaped around plain Parquet consumption.
- `WeightedSamplingReader` stops once one embedded reader exhausts its data.
- `InMemBatchedDataLoader` should not be reused for a second iterator pass.
