# API Reference

## Purpose

Read this when you need the verified Spark-converter call surface, cache behavior, or adapter-specific parameters.
The signatures below were checked against the installed package snapshot.

## Core entry points

| Symbol | Signature | Notes |
| --- | --- | --- |
| `make_spark_converter` | `make_spark_converter(df, parquet_row_group_size_bytes=33554432, compression_codec=None, dtype='float32')` | Materializes a Spark DataFrame into a cached parquet dataset and returns a converter object. |
| `SparkDatasetConverter` | `SparkDatasetConverter(cache_dir_url, file_urls, dataset_size)` | Holds the cached parquet dataset metadata and builds TF/Torch loaders. |
| `SparkDatasetConverter.delete` | `delete()` | Deletes the cached files for the converter. |

## Loader methods

| Symbol | Signature | Notes |
| --- | --- | --- |
| `make_tf_dataset` | `make_tf_dataset(batch_size=None, prefetch=None, num_epochs=None, workers_count=None, shuffling_queue_capacity=None, **petastorm_reader_kwargs)` | Returns a TensorFlow dataset context manager. |
| `make_torch_dataloader` | `make_torch_dataloader(batch_size=32, num_epochs=None, workers_count=None, shuffling_queue_capacity=0, data_loader_fn=None, **petastorm_reader_kwargs)` | Returns a Torch loader context manager. |

## Cache and compatibility helpers

| Symbol | Notes |
| --- | --- |
| `SparkDatasetConverter.PARENT_CACHE_DIR_URL_CONF` | Spark config key `petastorm.spark.converter.parentCacheDirUrl`. Must be set before creating a converter. |
| `register_delete_dir_handler(handler)` | Installs or resets the delete handler used when converter cache cleanup runs. |
| `_get_horovod_rank_and_size()` | Reads Horovod-compatible environment variables when present. |
| `_check_rank_and_size_consistent_with_horovod()` | Warns if the converter reader kwargs do not match the detected Horovod rank and size. |
| `_wait_file_available()` | Wait helper used while opening cached parquet files. |

## Behavior notes

- The converter caches a materialized parquet copy of the DataFrame.
- `batch_size=None` in `make_tf_dataset` currently defaults to 32 in this repository snapshot.
- `make_tf_dataset` and `make_torch_dataloader` close their readers when their context managers exit.
- If a Spark worker cannot reach the cache path, the converter path must be adjusted before conversion is useful.
- `make_spark_converter` is intended for Spark DataFrames, not for reader-side datasets.
