---
name: "read-datasets"
description: "Routes Petastorm dataset-reading workflows, including plain Python
  iteration, TensorFlow and PyTorch adapters, Spark RDD reads, row-group
  selection, NGrams, and throughput benchmarking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Read Datasets

Use this route when the user wants to open an existing Petastorm dataset or plain Parquet store and read samples back in Python,
TensorFlow, PyTorch, or Spark.
This route also owns predicates, sharding, row-group selectors, NGrams, shuffling, caching, and throughput measurement.

## Typical triggers

- "How do I read this Petastorm dataset?"
- "How do I use `make_reader` or `make_batch_reader`?"
- "How do I select row groups or filter rows?"
- "How do I get TensorFlow tensors or a PyTorch DataLoader?"
- "How do I benchmark reader throughput?"

## What belongs here

- `make_reader`
- `make_batch_reader`
- `Reader`
- row predicates and selectors
- sharding and epoch control
- `NGram`
- `WeightedSamplingReader`
- `tf_tensors`
- `make_petastorm_dataset`
- `DataLoader`, `BatchedDataLoader`, and `InMemBatchedDataLoader`
- `dataset_as_rdd`
- `petastorm-throughput.py`
- cache and cleanup behavior for reads

## What does not belong here

- dataset writing and schema construction
- metadata repair
- copy and filter workflows
- Spark DataFrame conversion into cached datasets

Use `sub-skills/create-datasets/` for those tasks.
Use `sub-skills/spark-converter/` when the starting point is a Spark DataFrame cache.

## Read this first

- `references/workflows.md` for end-to-end read recipes
- `references/api-reference.md` for verified signatures and semantics
- `references/cli-reference.md` for the throughput CLI
- `references/troubleshooting.md` for import-order, metadata, and adapter failures
- `scripts/smoke_read_minimal_dataset.py` for a tiny read-back smoke test
- `scripts/smoke_read_plain_parquet.py` for the plain Parquet batch-reader path
- `scripts/smoke_read_tensorflow.py` when TensorFlow support needs a quick check
- `scripts/smoke_read_torch.py` when PyTorch support needs a quick check

## How to choose a reading path

1. **Petastorm dataset or plain Parquet?**
   - Use `make_reader` for Petastorm datasets.
   - Use `make_batch_reader` for plain Parquet stores or when batch output is acceptable.
2. **Need row-level logic?**
   - Use `predicate`, `rowgroup_selector`, `shuffle_rows`, `shuffle_row_groups`, or `transform_spec`.
3. **Need framework integration?**
   - Use `tf_tensors` or `make_petastorm_dataset` for TensorFlow.
   - Use `DataLoader`, `BatchedDataLoader`, or `InMemBatchedDataLoader` for PyTorch.
4. **Need aggregation or mixed sampling?**
   - Use `NGram` or `WeightedSamplingReader`.
5. **Need Spark RDD access or timing?**
   - Use `dataset_as_rdd` or the throughput CLI.

## Boundary reminders

- `make_reader` expects a Petastorm dataset and will warn if the store lacks Petastorm metadata.
- `make_batch_reader` is the route for non-Petastorm Parquet data.
- `DataLoader` and `BatchedDataLoader` are not interchangeable: the batched variant is optimized for tensorable fields and the in-memory variant is single-use.
- PyTorch users should import `pyarrow` before importing `torch`.
- TensorFlow dataset repetition should usually be controlled through the reader's `num_epochs`, not by repeating the dataset blindly.

## Common tasks

### Read a Petastorm dataset in plain Python

1. Call `make_reader(dataset_url, ...)`.
2. Use `reader_pool_type='dummy'` for the smallest deterministic smoke checks.
3. Iterate rows and close the reader with a context manager.

### Read a non-Petastorm Parquet store

1. Call `make_batch_reader(dataset_url_or_urls, ...)`.
2. Limit `schema_fields` to the columns you actually need.
3. Treat returned objects as batches rather than single rows.

### Connect to TensorFlow

1. Build a reader.
2. Call `tf_tensors(reader)` or `make_petastorm_dataset(reader)`.
3. Consume the tensors inside a `tf.Session()` style loop.

### Connect to PyTorch

1. Import `pyarrow` before `torch`.
2. Wrap the reader in `DataLoader`, `BatchedDataLoader`, or `InMemBatchedDataLoader`.
3. Avoid nullable or string-heavy fields when you want tensor-only batches.

### Measure throughput

1. Use `petastorm-throughput.py` with a real dataset URL.
2. Start with the dummy or thread pool on a tiny dataset.
3. Increase cycles only after the basic path is working.

## When to stop and switch routes

- If the problem is schema creation, field encoding, or dataset layout, switch to `create-datasets`.
- If the problem is converting a Spark DataFrame cache into a loader, switch to `spark-converter`.
- If the problem is a URL or filesystem resolution issue, read the root filesystem reference first.
