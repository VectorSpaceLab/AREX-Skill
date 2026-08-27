---
name: "spark-converter"
description: "Routes Spark DataFrame conversion workflows that materialize
  cached parquet datasets and expose TensorFlow or PyTorch loaders through
  Petastorm."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Spark Converter

Use this route when the starting point is a Spark DataFrame that should be materialized once and reused many times as a TensorFlow dataset
or a PyTorch DataLoader.
This route owns the converter cache, cache cleanup, filesystem normalization, and the Spark-side API surface around
`make_spark_converter`.

## Typical triggers

- "How do I convert a Spark DataFrame into a TF dataset?"
- "How do I convert a Spark DataFrame into a PyTorch DataLoader?"
- "How do I set the converter cache directory?"
- "How do I delete converter cache files?"
- "Why does Spark converter cache cleanup or Horovod compatibility fail?"

## What belongs here

- `make_spark_converter`
- `SparkDatasetConverter`
- `make_tf_dataset`
- `make_torch_dataloader`
- converter cleanup and delete behavior
- parent cache directory configuration
- DBFS and filesystem normalization rules
- file availability waits for the converter cache
- Horovod rank/size compatibility checks

## What does not belong here

- raw dataset writing
- metadata repair
- reader-side `make_reader` and `make_batch_reader` workflows
- general Spark SQL or ML training that does not use the converter

Use `sub-skills/create-datasets/` for writing new datasets.
Use `sub-skills/read-datasets/` for consuming existing datasets directly.

## Read this first

- `references/workflows.md` for converter setup and adapter recipes
- `references/api-reference.md` for verified signatures and cache behavior
- `references/troubleshooting.md` for Spark, DBFS, cache, and optional backend failures
- `scripts/smoke_spark_converter.py` for a tiny end-to-end conversion check

## How to choose a converter path

1. **Starting from a Spark DataFrame?**
   - Use `make_spark_converter(df, ...)`.
2. **Need TensorFlow input?**
   - Call `converter.make_tf_dataset(...)`.
3. **Need PyTorch input?**
   - Call `converter.make_torch_dataloader(...)`.
4. **Need to clean up cache files?**
   - Call `converter.delete()` or register a custom delete handler if the filesystem needs special treatment.

## Boundary reminders

- `SparkDatasetConverter.PARENT_CACHE_DIR_URL_CONF` must be set before creating a converter.
- The converter caches a materialized parquet version of the DataFrame.
- The cache is reusable across TF or Torch loaders once the converter is created.
- `make_tf_dataset` and `make_torch_dataloader` are context managers that close their readers when the context exits.
- The converter can be used from remote Spark workers only when its cached files are available there too.

## Common tasks

### Create a converter

1. Set `petastorm.spark.converter.parentCacheDirUrl` on the Spark session.
2. Call `make_spark_converter(df)`.
3. Reuse the converter for one or more loaders.

### Build a TensorFlow dataset

1. Call `converter.make_tf_dataset(...)`.
2. Choose `batch_size`, `num_epochs`, and `shuffling_queue_capacity` as needed.
3. Train or evaluate inside the returned context manager.

### Build a PyTorch dataloader

1. Call `converter.make_torch_dataloader(...)`.
2. Choose `batch_size`, `num_epochs`, and `shuffling_queue_capacity` as needed.
3. Use the resulting loader in your model code.

### Delete the cache

1. Call `converter.delete()` after the loader is no longer needed.
2. If the filesystem needs a custom delete implementation, register it first.

## When to stop and switch routes

- If the starting point is raw rows or a schema definition, switch to `create-datasets`.
- If the starting point is an existing dataset instead of a Spark DataFrame, switch to `read-datasets`.
