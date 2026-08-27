---
name: "create-datasets"
description: "Routes Petastorm dataset creation, schema design, metadata repair,
  copy-and-filter workflows, and row-group indexing from Spark and existing
  Parquet data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Create Datasets

Use this route when the task starts from raw rows, a Spark DataFrame, or an existing Parquet store that needs Petastorm metadata,
copying, filtering, schema repair, or row-group indexing.

## Typical triggers

- "How do I create a Petastorm dataset?"
- "How do I define a schema or codec?"
- "How do I copy and filter an existing dataset?"
- "How do I regenerate Petastorm metadata?"
- "How do I build row-group indexes?"
- "How do I use the copy or metadata console tools?"

## What belongs here

- `Unischema` and `UnischemaField`
- `ScalarCodec`, `NdarrayCodec`, `CompressedNdarrayCodec`, `CompressedImageCodec`
- `dict_to_spark_row`
- `materialize_dataset`
- `get_schema` and `get_schema_from_dataset_url`
- `copy_dataset`
- `generate_petastorm_metadata`
- `build_rowgroup_index`
- `SingleFieldIndexer` and `FieldNotNullIndexer`
- filesystem URL resolution used while writing or repairing datasets
- the `petastorm-copy-dataset.py` and `petastorm-generate-metadata.py` commands

## What does not belong here

- consuming an already-created dataset
- TensorFlow and PyTorch adapter details beyond writer-side shape or schema concerns
- Spark DataFrame caching into reusable loaders

Use `sub-skills/read-datasets/` for reader work.
Use `sub-skills/spark-converter/` when the task is caching a Spark DataFrame for later loading.

## Read this first

- `references/workflows.md` for writing, copying, metadata repair, and indexing recipes
- `references/api-reference.md` for verified signatures and behavior
- `references/cli-reference.md` for the dataset copy and metadata commands
- `references/data-formats.md` for the on-disk layout and metadata keys
- `references/troubleshooting.md` for schema, Spark, URL, and metadata failures
- `scripts/smoke_make_minimal_dataset.py` for a tiny write smoke test
- `scripts/smoke_copy_dataset.py` for a copy-and-filter smoke test
- `scripts/smoke_generate_metadata.py` for a metadata-repair smoke test

## How to choose a creation path

1. **Starting from rows or a DataFrame?**
   - Define a `Unischema` and write through `materialize_dataset`.
2. **Need to rewrite an existing dataset?**
   - Use `copy_dataset` for subset/filter/repartition jobs.
3. **Need to restore reader compatibility?**
   - Use `generate_petastorm_metadata`.
4. **Need row-group acceleration?**
   - Use `build_rowgroup_index` with the matching indexer type.

## Boundary reminders

- Non-scalar fields need a codec.
- `materialize_dataset` is the writer-side contract that stamps Petastorm metadata onto the Parquet output.
- `copy_dataset` can narrow columns and drop rows with nulls in selected fields.
- `generate_petastorm_metadata` can infer the schema from the dataset when metadata already exists, or use a supplied unischema class string.
- `build_rowgroup_index` expects compatible indexers and a writable dataset metadata location.

## Common tasks

### Create a new dataset

1. Define a schema with `Unischema`.
2. Convert dictionaries into Spark rows with `dict_to_spark_row`.
3. Wrap the write in `materialize_dataset`.
4. Write to a `file://`, `hdfs://`, `s3://`, or compatible URL.

### Repair or regenerate metadata

1. Open the existing dataset URL.
2. Call `generate_petastorm_metadata` or the CLI wrapper.
3. Reopen the dataset with `make_reader` to confirm the repair.

### Copy or filter a dataset

1. Decide which columns should survive the copy.
2. Decide which fields must remain non-null.
3. Optionally repartition before write.
4. Read the result back to confirm the shape.

### Build a row-group index

1. Create an indexer object for the field you want to accelerate.
2. Call `build_rowgroup_index` from a Spark context.
3. Use the resulting selector on the read side.

## When to stop and switch routes

- If the user only wants to open the data, switch to `read-datasets`.
- If the user wants to convert a Spark DataFrame into a reusable cached loader, switch to `spark-converter`.
