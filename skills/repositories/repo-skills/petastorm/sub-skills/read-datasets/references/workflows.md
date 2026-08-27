# Workflows

## Purpose

Read this when you need an end-to-end recipe for opening datasets, adapting them to frameworks, or benchmarking a reader path.
The recipes below reflect the installed API surface and the repository examples/tests.

## 1) Read a Petastorm dataset in plain Python

1. Start with a dataset URL such as `file://...`, `hdfs://...`, or `s3://...`.
2. Call `make_reader(dataset_url, ...)`.
3. Use `reader_pool_type='dummy'` for the smallest smoke check or `thread` for the common default path.
4. Iterate rows and stop the reader with a context manager.

```python
from petastorm import make_reader

with make_reader("file:///tmp/petastorm-dataset", reader_pool_type="dummy", num_epochs=1) as reader:
    for row in reader:
        print(row.id)
```

### Useful knobs

- `schema_fields` to narrow columns
- `predicate` to filter rows
- `rowgroup_selector` to select row groups using metadata
- `shuffle_rows` and `shuffle_row_groups` to decorrelate reads
- `cache_type='local-disk'` for disk-backed caching
- `transform_spec` to change the row shape after decode

## 2) Read a plain Parquet store

1. Use `make_batch_reader(dataset_url_or_urls, ...)`.
2. Treat the returned object as batch-oriented.
3. Restrict `schema_fields` to the columns you need.
4. Use `num_epochs=1` for one-pass smoke checks.

```python
from petastorm import make_batch_reader

with make_batch_reader("file:///tmp/plain-parquet", reader_pool_type="dummy", num_epochs=1) as reader:
    for batch in reader:
        print(batch.id)
```

### When to prefer this path

- The store was not generated with `materialize_dataset`.
- You only need primitive columns.
- Batch output is more convenient than row-wise output.

## 3) Attach TensorFlow

### `tf_tensors`

1. Build a reader.
2. Call `tf_tensors(reader)`.
3. Run the tensors inside a TensorFlow session.

```python
import tensorflow.compat.v1 as tf
from petastorm import make_reader
from petastorm.tf_utils import tf_tensors

with make_reader("file:///tmp/petastorm-dataset", num_epochs=1) as reader:
    tensors = tf_tensors(reader)
    with tf.Session() as sess:
        sample = sess.run(tensors)
        print(sample.id)
```

### `make_petastorm_dataset`

1. Build a reader.
2. Convert it with `make_petastorm_dataset(reader)`.
3. Apply `map`, `batch`, `prefetch`, or `concatenate` as needed.
4. Prefer reader epochs or cache-before-repeat rather than repeating the dataset blindly.

```python
with make_reader("file:///tmp/petastorm-dataset", num_epochs=1) as reader:
    dataset = make_petastorm_dataset(reader)
    iterator = dataset.make_one_shot_iterator()
```

## 4) Attach PyTorch

1. Import `pyarrow` before `torch`.
2. Choose `DataLoader` for row-wise reading or `BatchedDataLoader` for tensor-only flows.
3. Use `InMemBatchedDataLoader` only when the dataset fits in memory and you only need one pass.
4. Avoid nullable or string-heavy fields when you want clean tensor batches.

```python
import pyarrow  # keep this before torch
import torch
from petastorm import make_reader
from petastorm.pytorch import DataLoader

with DataLoader(make_reader("file:///tmp/petastorm-dataset", num_epochs=1), batch_size=4) as loader:
    batch = next(iter(loader))
    print(batch["id"])
```

## 5) Use row-group selectors, predicates, and NGrams

- Use `predicate` for row filtering based on values.
- Use `rowgroup_selector` when you already know the row groups you want.
- Use `NGram` when you need time-windowed sequences keyed by a timestamp field.
- Use `WeightedSamplingReader` when you want to sample from multiple readers with fixed probabilities.

### Important NGram constraint

Rows must be sorted by the timestamp field expected by the `NGram`. If the data is not sorted, the reader should fail fast instead of quietly returning a wrong sequence.

## 6) Read into Spark or benchmark throughput

- Use `dataset_as_rdd()` when you want a Spark RDD of namedtuples.
- Use `petastorm-throughput.py` when you need a quick timing or memory check on a reader path.

### Practical routing rule

If you are still deciding between `make_reader` and `make_batch_reader`, use this quick check:

- Petastorm metadata present, row-wise logic needed, or framework adapters needed -> `make_reader`
- Plain Parquet store or batch-oriented consumption -> `make_batch_reader`
